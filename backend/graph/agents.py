"""The agent nodes and the supervisor that routes between them.

    START -> supervisor -> retriever -> supervisor -> analyst -> supervisor -> writer
                 ^                                                              |
                 |  (reflection on)  critic -> supervisor --revise--> writer ---+
                 +--------------------------------------------------------------+
             supervisor -> approval (human interrupt) -> END

Hierarchy: workers never call each other; they all report back to the
supervisor, which decides the next step. The supervisor uses the LLM once, to
plan (split the question into sub-questions). After that, routing is plain code
in `route()`. That keeps it cheap, testable and impossible to loop forever.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END
from langgraph.types import Command, interrupt

from backend.audit.logger import audit_logger
from backend.graph.react import react_loop
from backend.graph.state import Critique, Evidence, Plan, VajraState
from backend.graph.tools import ToolRegistry
from backend.graph.tracing import node_span
from backend.llm.base import ChatMessage, LLMClient

MAX_EVIDENCE = 6
NOT_FOUND = "Not found in the provided documents."


@dataclass
class Deps:
    llm: LLMClient
    tools: ToolRegistry


def numbered(evidence: list[Evidence]) -> str:
    return "\n\n".join(f"[{i}] ({e['citation']}) {e['text']}" for i, e in enumerate(evidence, 1))


def numbered_calcs(calcs: list[dict]) -> str:
    """Calculator outputs are facts too: the Writer may cite them and the Critic must accept them."""
    if not calcs:
        return "(none)"
    return "\n".join(f"[C{i}] {c['expression']} = {c['result']}" for i, c in enumerate(calcs, 1))


# ---------------- routing (pure function, unit-tested) ----------------
def route(state: VajraState) -> str:
    if state.get("status") in ("approved", "rejected", "failed"):
        return END
    if not state.get("plan"):
        return "supervisor"
    if not state.get("evidence"):
        return "retriever"
    if state.get("analysis") is None:
        return "analyst"
    if not state.get("draft"):
        return "writer"
    if state.get("reflection"):
        version = state.get("draft_version", 0)
        crit = state.get("critique")
        if crit is None or crit["draft_version"] != version:
            return "critic"
        # draft_version 1 is the first draft, so N revisions allow versions up to N + 1.
        if crit["verdict"] == "revise" and version <= state.get("max_revisions", 2):
            return "writer"
    return "approval"


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "sub_questions": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "needs_calculation": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": ["sub_questions", "needs_calculation", "rationale"],
}


def make_supervisor(d: Deps):
    def supervisor(state: VajraState) -> Command:
        update: dict[str, Any] = {"steps": ["supervisor"]}
        if not state.get("plan"):
            with node_span(state["run_id"], "supervisor"):
                r = d.llm.chat([
                    ChatMessage("system", "You plan research over industrial plant documents. Split the user's question "
                                          "into at most 3 short search sub-questions (fewer if it is simple) and say whether "
                                          "answering it needs arithmetic. Return JSON."),
                    ChatMessage("user", state["question"]),
                ], json_schema=PLAN_SCHEMA)
                try:
                    plan: Plan = json.loads(r.text)
                    plan["sub_questions"] = [s for s in plan.get("sub_questions", []) if s.strip()][:3]
                except json.JSONDecodeError:
                    plan = Plan(sub_questions=[], needs_calculation=False, rationale="planner output unparseable")
            update.update(plan=plan, status="working")
            audit_logger.log("AGENT_PLAN", "SUPERVISOR", f"Run {state['run_id']}: {len(plan['sub_questions'])} sub-questions",
                             metadata={"run_id": state["run_id"]})
        nxt = route({**state, **update})
        return Command(update=update, goto=nxt)

    return supervisor


def make_retriever(d: Deps):
    def retriever(state: VajraState) -> dict:
        run_id = state["run_id"]
        with node_span(run_id, "retriever"):
            found: list[Evidence] = []
            log: list[dict] = []

            def add(results: list[dict]) -> None:
                for e in results:
                    if len(found) < MAX_EVIDENCE and all(f["chunk_id"] != e["chunk_id"] for f in found):
                        found.append(Evidence(**e))

            # Deterministic seed: always search the question and each planned sub-question.
            seeds = [(state["question"], 5)] + [(q, 3) for q in state["plan"]["sub_questions"]]
            for query, k in seeds:
                out = d.tools.call("search_documents", {"query": query, "k": k}, run_id)
                log.append({"agent": "retriever", "tool": "search_documents", "query": query, "ok": out.ok, "cached": out.cached})
                if out.ok:
                    add(out.result)

            # ReAct step: the agent looks at what it has and may run extra searches.
            have = "\n".join(f"[{i}] {e['citation']}: {e['text'][:160]}" for i, e in enumerate(found, 1))
            rr = react_loop(
                d.llm, d.tools, run_id=run_id, tool_names=["search_documents"], max_steps=2,
                system="You are the Retriever agent. Decide whether the passages already found are enough to answer "
                       "the question. If something is missing, search for it with a focused query; otherwise finish.",
                task=f"Question: {state['question']}\n\nPassages found so far:\n{have}",
                observe=lambda res: "\n".join(f"{x['citation']}: {x['text'][:160]}" for x in res) if isinstance(res, list) else str(res),
            )
            for tool, result in rr.outputs:
                add(result)
            log += [{"agent": "retriever", **s} for s in rr.steps]
        if not found:  # nothing to ground an answer in; stop instead of looping back here
            return {"status": "failed", "error": "no evidence retrieved", "tool_log": log, "steps": ["retriever"]}
        return {"evidence": found, "tool_log": log, "steps": ["retriever"]}

    return retriever


def make_analyst(d: Deps):
    def analyst(state: VajraState) -> dict:
        run_id = state["run_id"]
        with node_span(run_id, "analyst"):
            ev = state["evidence"]
            rr = react_loop(
                d.llm, d.tools, run_id=run_id, tool_names=["calculator", "extract_fields"], max_steps=3,
                context={"evidence": ev},
                system="You are the Analyst agent. Using ONLY the numbered evidence below, work out the facts needed to "
                       "answer the question. If the question needs arithmetic, use calculator to compute exactly the "
                       "quantity asked for (for 'by how much' use a difference, not a percentage). Use extract_fields "
                       "to pull exact values. Then finish with short analysis notes that cite evidence like [2]. "
                       "Do not do arithmetic the question does not ask for.\n\nEVIDENCE:\n" + numbered(ev),
                task=f"Question: {state['question']}\nPlanner says arithmetic needed: {state['plan']['needs_calculation']}",
            )
            calcs = [r for t, r in rr.outputs if t == "calculator"]
            notes = rr.final.strip()
            if not notes:  # step cap hit without finishing: keep whatever the tools produced
                notes = "; ".join(f"{t}: {json.dumps(r)[:300]}" for t, r in rr.outputs) or "No analysis produced."
        return {"analysis": notes, "calculations": calcs, "tool_log": [{"agent": "analyst", **s} for s in rr.steps],
                "steps": ["analyst"]}

    return analyst


WRITER_SYSTEM = (
    "You are the Writer agent for VAJRA, an on-premise assistant for maintenance engineers. Answer the question in "
    "one to three plain sentences using ONLY the numbered evidence and calculator results. End each sentence with "
    "its sources, like [1] or [2][C1]. Do not copy the bracketed file labels or the words 'CALCULATOR'/'EVIDENCE' into "
    f"the answer. If the evidence does not answer the question, reply exactly: {NOT_FOUND}"
)


def make_writer(d: Deps):
    def writer(state: VajraState) -> dict:
        with node_span(state["run_id"], "writer"):
            msg = (f"EVIDENCE:\n{numbered(state['evidence'])}\n\nCALCULATOR RESULTS:\n"
                   f"{numbered_calcs(state.get('calculations') or [])}\n\nANALYST NOTES:\n{state.get('analysis') or ''}"
                   f"\n\nQUESTION: {state['question']}")
            crit = state.get("critique")
            if crit and crit["verdict"] == "revise":
                msg += (f"\n\nYOUR PREVIOUS DRAFT:\n{state['draft']}\n\nREVIEWER FEEDBACK (fix this; remove or correct "
                        f"any claim the evidence does not support):\n{crit['feedback']}\nUnsupported claims: "
                        f"{json.dumps(crit['unsupported_claims'])}")
            r = d.llm.chat([ChatMessage("system", WRITER_SYSTEM), ChatMessage("user", msg)])
        return {"draft": r.text.strip(), "draft_version": state.get("draft_version", 0) + 1, "steps": ["writer"]}

    return writer


CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {"type": "array", "items": {"type": "object", "properties": {
            "claim": {"type": "string"}, "supported": {"type": "boolean"},
            "evidence_ids": {"type": "array", "items": {"type": "integer"}}},
            "required": ["claim", "supported", "evidence_ids"]}},
        "feedback": {"type": "string"},
    },
    "required": ["claims", "feedback"],
}


def make_critic(d: Deps):
    def critic(state: VajraState) -> dict:
        with node_span(state["run_id"], "critic"):
            draft = state["draft"] or ""
            version = state.get("draft_version", 1)
            if NOT_FOUND.lower() in draft.lower():
                crit = Critique(draft_version=version, unsupported_claims=[], verdict="approve", feedback="abstained")
            else:
                r = d.llm.chat([
                    ChatMessage("system", "You are the Critic agent. Split the DRAFT into atomic factual claims (ignore "
                                          "[n] markers). A claim is supported if the EVIDENCE states it, it follows directly "
                                          "from it, or it is a CALCULATOR RESULT (those are exact and already verified). "
                                          "List the evidence numbers that support each claim. In feedback, say precisely "
                                          "what to remove or fix. Return JSON."),
                    ChatMessage("user", f"EVIDENCE:\n{numbered(state['evidence'])}\n\nCALCULATOR RESULTS:\n"
                                        f"{numbered_calcs(state.get('calculations') or [])}\n\nDRAFT:\n{draft}"),
                ], json_schema=CRITIC_SCHEMA)
                try:
                    out = json.loads(r.text)
                    bad = [c["claim"] for c in out.get("claims", []) if not c.get("supported")]
                    # The verdict is computed from the claim list, not asked for, so the model can't
                    # say "approve" while listing unsupported claims.
                    crit = Critique(draft_version=version, unsupported_claims=bad,
                                    verdict="revise" if bad else "approve", feedback=out.get("feedback", ""))
                except json.JSONDecodeError:
                    crit = Critique(draft_version=version, unsupported_claims=[], verdict="approve",
                                    feedback="critic output unparseable; passed through")
        return {"critique": crit, "steps": ["critic"]}

    return critic


def make_approval(d: Deps):
    def approval(state: VajraState) -> dict:
        # NOTE: on resume LangGraph re-runs this node from the top, so nothing with side
        # effects may happen before interrupt(). Audit logging is after it.
        if state.get("auto_approve"):
            decision = {"decision": "approve", "reviewer": "auto (eval mode)", "notes": ""}
        else:
            decision = interrupt({
                "run_id": state["run_id"], "question": state["question"], "draft": state["draft"],
                "citations": [e["citation"] for e in state["evidence"]],
                "critique": state.get("critique"),
                "instructions": "Resume with {'decision': 'approve'|'reject', 'reviewer': str, 'notes': str}",
            })
        approved = str(decision.get("decision", "")).lower() == "approve"
        with node_span(state["run_id"], "approval"):
            pass  # records the moment the decision was applied (no LLM work here)
        audit_logger.log("HUMAN_APPROVAL_DECISION", decision.get("reviewer", "unknown"),
                         f"Run {state['run_id']} {'APPROVED' if approved else 'REJECTED'}: {decision.get('notes', '')}",
                         metadata={"run_id": state["run_id"]})
        return {
            "approval": {"decision": "approve" if approved else "reject", "reviewer": decision.get("reviewer", "unknown"),
                         "notes": decision.get("notes", "")},
            "final_answer": state["draft"] if approved else None,
            "status": "approved" if approved else "rejected",
            "steps": ["approval"],
        }

    return approval
