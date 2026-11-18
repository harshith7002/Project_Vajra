"""Typed, idempotent tools for the agents.

Typed: every tool declares a Pydantic model for its arguments. Model output is
validated against it before anything runs; a bad call becomes an error message
the agent can read and fix (it is never executed with garbage arguments).

Idempotent: a call is identified by sha256(tool name + canonical JSON args).
Results are stored in a SQLite table keyed by (run_id, call key). If a node is
retried, or a paused run is resumed in a new process, the same call returns the
stored result instead of running again. That matters for tools with cost or
side effects; for search it also guarantees the agent sees the same evidence.
"""
from __future__ import annotations

import ast
import hashlib
import json
import operator
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.config import settings
from backend.graph.tracing import record_tool
from backend.llm.base import ChatMessage, LLMClient
from backend.rag.retriever import HybridRetriever


# ---------- argument schemas ----------
class SearchArgs(BaseModel):
    query: str = Field(min_length=3, max_length=300, description="What to look for in the plant documents")
    k: int = Field(default=4, ge=1, le=8, description="How many passages to return")


class CalculatorArgs(BaseModel):
    expression: str = Field(min_length=1, max_length=200, description="Arithmetic only, e.g. (7.8 - 7.0) / 7.0 * 100")


class ExtractArgs(BaseModel):
    fields: list[str] = Field(min_length=1, max_length=6, description="Names of values to pull out, e.g. ['vibration limit']")
    evidence_ids: list[int] = Field(default_factory=list, max_length=8, description="Evidence numbers to read; empty = all")

    @field_validator("fields")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        v = [f.strip() for f in v if f.strip()]
        if not v:
            raise ValueError("fields must contain at least one non-empty name")
        return v


# ---------- safe calculator ----------
_OPS: dict[type, Callable[..., float]] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def safe_eval(expression: str) -> float:
    """Evaluate +-*/%** on numbers by walking the AST. No names, calls or attributes, so no eval() risk."""

    def walk(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("exponent too large")
            return _OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.operand))
        raise ValueError(f"unsupported expression element: {type(node).__name__}")

    return walk(ast.parse(expression.replace("^", "**"), mode="eval"))


# ---------- idempotency store ----------
class ToolResultStore:
    def __init__(self, path: Path | None = None) -> None:
        path = path or (settings.index_dir / "tool_calls.sqlite")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS tool_calls (run_id TEXT, call_key TEXT, tool TEXT, args TEXT, "
                         "result TEXT, created REAL, PRIMARY KEY (run_id, call_key))")
        self._lock = threading.Lock()

    def get(self, run_id: str, key: str) -> Any | None:
        with self._lock:
            row = self._db.execute("SELECT result FROM tool_calls WHERE run_id=? AND call_key=?", (run_id, key)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, run_id: str, key: str, tool: str, args: dict, result: Any) -> None:
        with self._lock:
            self._db.execute("INSERT OR IGNORE INTO tool_calls VALUES (?,?,?,?,?,?)",
                             (run_id, key, tool, json.dumps(args, sort_keys=True), json.dumps(result), time.time()))
            self._db.commit()


def call_key(tool: str, args: dict) -> str:
    return hashlib.sha256(f"{tool}|{json.dumps(args, sort_keys=True)}".encode()).hexdigest()[:16]


@dataclass
class ToolOutcome:
    ok: bool
    result: Any
    cached: bool
    key: str | None


@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[[BaseModel, dict], Any]  # (validated args, context) -> JSON-serialisable result

    def schema_line(self) -> str:
        props = self.args_model.model_json_schema()["properties"]
        args = ", ".join(f"{k}: {v.get('type', 'any')} ({v.get('description', '')})" for k, v in props.items())
        return f"- {self.name}({args}): {self.description}"


class ToolRegistry:
    def __init__(self, retriever: HybridRetriever, llm: LLMClient, store: ToolResultStore | None = None) -> None:
        self.retriever, self.llm = retriever, llm
        self.store = store or ToolResultStore()
        self.tools: dict[str, Tool] = {
            t.name: t for t in (
                Tool("search_documents", "Hybrid search over the indexed plant documents; returns cited passages.",
                     SearchArgs, self._search),
                Tool("calculator", "Exact arithmetic. Use it instead of doing maths in your head.",
                     CalculatorArgs, lambda a, ctx: {"expression": a.expression, "result": round(safe_eval(a.expression), 6)}),
                Tool("extract_fields", "Pull named values (numbers, limits, names) out of the evidence as JSON.",
                     ExtractArgs, self._extract),
            )
        }

    def call(self, name: str, raw_args: Any, run_id: str, context: dict | None = None) -> ToolOutcome:
        tool = self.tools.get(name)
        if tool is None:
            return ToolOutcome(False, f"Unknown tool '{name}'. Available: {', '.join(self.tools)}", False, None)
        try:
            args = tool.args_model.model_validate(raw_args or {})
        except ValidationError as e:
            msgs = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
            return ToolOutcome(False, f"Invalid arguments for {name}: {msgs}", False, None)

        canonical = args.model_dump()
        key = call_key(name, canonical)
        t0 = time.perf_counter()
        cached = self.store.get(run_id, key)
        if cached is not None:
            record_tool(name, True, time.perf_counter() - t0)
            return ToolOutcome(True, cached, True, key)
        try:
            result = tool.fn(args, context or {})
        except Exception as e:  # tool errors are observations, not crashes
            record_tool(name, False, time.perf_counter() - t0)
            return ToolOutcome(False, f"{name} failed: {e}", False, key)
        self.store.put(run_id, key, name, canonical, result)
        record_tool(name, False, time.perf_counter() - t0)
        return ToolOutcome(True, result, False, key)

    # ---------- implementations ----------
    def _search(self, a: SearchArgs, ctx: dict) -> list[dict]:
        hits = self.retriever.search(a.query, k=a.k)
        return [{"chunk_id": h.chunk_id, "citation": h.citation(), "text": h.text, "score": round(h.score, 4)} for h in hits]

    def _extract(self, a: ExtractArgs, ctx: dict) -> dict:
        evidence: list[dict] = ctx.get("evidence", [])
        chosen = [(i, e) for i, e in enumerate(evidence, 1) if not a.evidence_ids or i in a.evidence_ids]
        text = "\n\n".join(f"[{i}] {e['text']}" for i, e in chosen)
        schema = {
            "type": "object",
            "properties": {f: {"type": "object", "properties": {"value": {"type": "string"}, "evidence_id": {"type": "integer"}},
                               "required": ["value", "evidence_id"]} for f in a.fields},
            "required": a.fields,
        }
        r = self.llm.chat([
            ChatMessage("system", "Extract each requested field from the evidence. value='not stated' if absent. "
                                  "evidence_id is the [n] the value came from (0 if absent). Return JSON."),
            ChatMessage("user", f"EVIDENCE:\n{text}\n\nFIELDS: {', '.join(a.fields)}"),
        ], json_schema=schema)
        try:
            return json.loads(r.text)
        except json.JSONDecodeError:
            raise ValueError("model did not return valid JSON")
