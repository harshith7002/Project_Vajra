"""Per-node tracing: latency, tokens, tokens/sec, retries and estimated cost.

Every number comes from a measurement: wall-clock timers and the token counts
the model server returns. Cost = tokens x the rate in config/prices.json, so it
is an *estimate* only in the sense that the rates are whatever you configure.

One trace file per run: data/traces/<run_id>.json
One summary row per run:  data/traces/summary.csv
"""
from __future__ import annotations

import contextvars
import csv
import json
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

import httpx

from backend.config import REPO_ROOT
from backend.llm.base import ChatMessage, LLMClient, LLMResult

TRACE_DIR = REPO_ROOT / "data" / "traces"
PRICES_FILE = REPO_ROOT / "config" / "prices.json"

_current_node: contextvars.ContextVar[str] = contextvars.ContextVar("vajra_node", default="unscoped")
_current_run: contextvars.ContextVar[str] = contextvars.ContextVar("vajra_run", default="")


def load_prices(path: Path = PRICES_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"models": {}, "default": {}}


def cost_usd(model: str, in_tok: int, out_tok: int, prices: dict[str, Any]) -> float:
    rate = prices.get("models", {}).get(model) or prices.get("default") or {}
    return (in_tok * float(rate.get("input_per_1m") or 0) + out_tok * float(rate.get("output_per_1m") or 0)) / 1e6


@dataclass
class LLMCallRecord:
    node: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    tokens_per_s: float  # end-to-end: output tokens / whole call latency
    retries: int
    cost_usd: float
    ok: bool = True
    prefill_tokens_per_s: float = 0.0  # prompt processing speed reported by the server
    decode_tokens_per_s: float = 0.0  # generation speed reported by the server


@dataclass
class NodeSpan:
    node: str
    started_at: float
    latency_s: float = 0.0
    llm_calls: list[LLMCallRecord] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class RunTrace:
    def __init__(self, run_id: str, system: str, question: str) -> None:
        self.run_id, self.system, self.question = run_id, system, question
        self.spans: list[NodeSpan] = []
        self.started_at = time.time()
        self._lock = threading.Lock()

    def span_for(self, node: str) -> NodeSpan:
        with self._lock:
            span = NodeSpan(node, time.time())
            self.spans.append(span)
            return span

    def current(self) -> NodeSpan:
        node = _current_node.get()
        for s in reversed(self.spans):
            if s.node == node:
                return s
        return self.span_for(node)

    # ---------- aggregates ----------
    def totals(self) -> dict[str, Any]:
        calls = [c for s in self.spans for c in s.llm_calls]
        in_tok = sum(c.input_tokens for c in calls)
        out_tok = sum(c.output_tokens for c in calls)
        gen_s = sum(c.latency_s for c in calls)
        dec = [c.decode_tokens_per_s for c in calls if c.decode_tokens_per_s]
        pre = [c.prefill_tokens_per_s for c in calls if c.prefill_tokens_per_s]
        return {
            "run_id": self.run_id, "system": self.system,
            "wall_s": round(sum(s.latency_s for s in self.spans), 2),
            "llm_calls": len(calls), "input_tokens": in_tok, "output_tokens": out_tok,
            "tokens_per_s": round(out_tok / gen_s, 2) if gen_s else 0.0,
            "decode_tokens_per_s": round(sum(dec) / len(dec), 2) if dec else 0.0,
            "prefill_tokens_per_s": round(sum(pre) / len(pre), 2) if pre else 0.0,
            "retries": sum(c.retries for c in calls),
            "tool_calls": sum(len(s.tool_calls) for s in self.spans),
            "tool_cache_hits": sum(1 for s in self.spans for t in s.tool_calls if t.get("cached")),
            "cost_usd": round(sum(c.cost_usd for c in calls), 6),
            "nodes": ">".join(s.node for s in self.spans),
        }

    def save_json_only(self, directory: Path | None = None) -> Path:
        """Snapshot used while a run is paused for approval (no summary row yet)."""
        directory = directory or TRACE_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.run_id}.json"
        path.write_text(json.dumps({"run_id": self.run_id, "system": self.system, "question": self.question,
                                    "totals": self.totals(), "spans": [asdict(s) for s in self.spans]}, indent=2))
        return path

    @classmethod
    def from_file(cls, path: Path) -> "RunTrace":
        data = json.loads(path.read_text(encoding="utf-8"))
        t = cls(data["run_id"], data["system"], data["question"])
        for s in data["spans"]:
            calls = [LLMCallRecord(**c) for c in s.pop("llm_calls")]
            t.spans.append(NodeSpan(**s, llm_calls=calls))
        return t

    def save(self, directory: Path | None = None) -> Path:
        directory = directory or TRACE_DIR
        path = self.save_json_only(directory)
        summary = directory / "summary.csv"
        row = self.totals()
        new = not summary.exists()
        with summary.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)
        return path


class TraceRegistry:
    """Run id -> RunTrace, so graph nodes (which only see state) can find their trace."""

    def __init__(self) -> None:
        self._traces: dict[str, RunTrace] = {}

    def start(self, run_id: str, system: str, question: str) -> RunTrace:
        self._traces[run_id] = RunTrace(run_id, system, question)
        return self._traces[run_id]

    def get(self, run_id: str) -> RunTrace:
        if run_id not in self._traces:
            # A run resumed in a new process continues the trace it saved while paused.
            saved = TRACE_DIR / f"{run_id}.json"
            self._traces[run_id] = RunTrace.from_file(saved) if saved.exists() else RunTrace(run_id, "unknown", "")
        return self._traces[run_id]

    def pop(self, run_id: str) -> RunTrace | None:
        return self._traces.pop(run_id, None)


traces = TraceRegistry()


@contextmanager
def node_span(run_id: str, node: str) -> Iterator[NodeSpan]:
    """Time one node execution and make it the target for LLM/tool records."""
    trace = traces.get(run_id)
    span = trace.span_for(node)
    tok_node, tok_run = _current_node.set(node), _current_run.set(run_id)
    t0 = time.perf_counter()
    try:
        yield span
    except Exception as e:  # recorded, then re-raised for LangGraph's retry policy
        span.error = f"{type(e).__name__}: {e}"
        raise
    finally:
        span.latency_s = round(time.perf_counter() - t0, 3)
        _current_node.reset(tok_node)
        _current_run.reset(tok_run)


def record_tool(name: str, cached: bool, latency_s: float) -> None:
    run_id = _current_run.get()
    if run_id:
        traces.get(run_id).current().tool_calls.append({"tool": name, "cached": cached, "latency_s": round(latency_s, 3)})


class TracedLLM:
    """Wraps any LLMClient: retries transient failures and records every call."""

    TRANSIENT = (httpx.TimeoutException, httpx.TransportError)

    def __init__(self, inner: LLMClient, max_retries: int = 2, prices: dict | None = None) -> None:
        self.inner = inner
        self.max_retries = max_retries
        self.prices = prices if prices is not None else load_prices()
        self.provider, self.model = inner.provider, inner.model

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.inner.embed(texts)

    def chat(self, messages: list[ChatMessage], **kw: Any) -> LLMResult:
        retries = 0
        while True:
            try:
                result = self.inner.chat(messages, **kw)
                break
            except self.TRANSIENT:
                if retries >= self.max_retries:
                    self._record(None, retries)
                    raise
                retries += 1
                time.sleep(0.5 * 2**retries)
        self._record(result, retries)
        return result

    def _record(self, r: LLMResult | None, retries: int) -> None:
        run_id = _current_run.get()
        if not run_id:
            return
        node = _current_node.get()
        def rate(tokens: int, ns: Any) -> float:
            return round(tokens / (ns / 1e9), 2) if ns else 0.0

        rec = (LLMCallRecord(node, r.model, r.input_tokens, r.output_tokens, round(r.latency_s, 3),
                             round(r.tokens_per_s, 2), retries, cost_usd(r.model, r.input_tokens, r.output_tokens, self.prices),
                             prefill_tokens_per_s=rate(r.input_tokens, r.raw.get("prompt_eval_duration")),
                             decode_tokens_per_s=rate(r.output_tokens, r.raw.get("eval_duration")))
               if r else LLMCallRecord(node, self.model, 0, 0, 0.0, 0.0, retries, 0.0, ok=False))
        traces.get(run_id).current().llm_calls.append(rec)
