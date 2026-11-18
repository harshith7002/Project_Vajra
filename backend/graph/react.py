"""A small ReAct loop: Reason -> Act (call a tool) -> Observe -> repeat.

Each step the model must return JSON matching ACTION_SCHEMA (enforced by Ollama
structured outputs), e.g.
    {"thought": "I need the SOP threshold", "action": "search_documents",
     "args": {"query": "SOP vibration overhaul threshold"}, "final": ""}
The tool's Pydantic schema validates `args`; errors go back as the observation.
The loop stops when the model picks "finish" or after `max_steps` (hard cap so a
small model cannot loop forever).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from backend.graph.tools import ToolRegistry
from backend.llm.base import ChatMessage, LLMClient


def action_schema(tool_names: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "thought": {"type": "string"},
            "action": {"type": "string", "enum": [*tool_names, "finish"]},
            "args": {"type": "object"},
            "final": {"type": "string"},
        },
        "required": ["thought", "action", "args", "final"],
    }


@dataclass
class ReactResult:
    final: str
    steps: list[dict[str, Any]] = field(default_factory=list)  # thought/action/args/observation per step
    outputs: list[tuple[str, Any]] = field(default_factory=list)  # (tool, result) for successful calls
    hit_step_cap: bool = False


def _short(obj: Any, limit: int = 900) -> str:
    s = obj if isinstance(obj, str) else json.dumps(obj)
    return s if len(s) <= limit else s[:limit] + " ...(truncated)"


def react_loop(
    llm: LLMClient,
    registry: ToolRegistry,
    *,
    system: str,
    task: str,
    tool_names: list[str],
    run_id: str,
    max_steps: int,
    context: dict | None = None,
    observe: Any = _short,
) -> ReactResult:
    tools_text = "\n".join(registry.tools[n].schema_line() for n in tool_names)
    sys_prompt = (f"{system}\n\nTools:\n{tools_text}\n- finish: stop and put your answer in 'final'.\n\n"
                  "Each turn return JSON with thought, action, args (the tool's arguments as an object, {} for finish) "
                  "and final ('' unless action is finish).")
    out = ReactResult(final="")
    transcript = ""
    for step in range(max_steps):
        r = llm.chat([ChatMessage("system", sys_prompt),
                      ChatMessage("user", f"{task}\n\n{transcript}Step {step + 1} of at most {max_steps}. What next?")],
                     json_schema=action_schema(tool_names))
        try:
            move = json.loads(r.text)
        except json.JSONDecodeError:
            out.steps.append({"error": "unparseable action", "raw": r.text[:200]})
            transcript += "Observation: your last reply was not valid JSON.\n"
            continue
        action, args = move.get("action"), move.get("args") or {}
        if action == "finish":
            out.final = move.get("final", "")
            out.steps.append({"thought": move.get("thought", ""), "action": "finish"})
            return out
        outcome = registry.call(action, args, run_id, context)
        if outcome.ok:
            out.outputs.append((action, outcome.result))
        obs = observe(outcome.result) if outcome.ok else f"ERROR: {outcome.result}"
        out.steps.append({"thought": move.get("thought", ""), "action": action, "args": args,
                          "ok": outcome.ok, "cached": outcome.cached})
        transcript += (f"Thought: {move.get('thought', '')}\nAction: {action} {json.dumps(args)}\n"
                       f"Observation: {obs}\n\n")
    out.hit_step_cap = True
    return out
