"""Run / resume entry points used by the eval scripts (and the API in Phase 4).

Three systems share the same retriever, model and tracing so the comparison is fair:
  single        one retrieval + one LLM call (the Phase 1 RAG answerer)
  multi         supervisor -> retriever -> analyst -> writer -> approval
  multi_reflect same, plus Critic -> Writer revision loop (up to max_revisions)
"""
from __future__ import annotations

import uuid
from typing import Any, Literal

from langgraph.types import Command

from backend.graph.agents import Deps
from backend.graph.build import build_graph
from backend.graph.state import VajraState
from backend.graph.tracing import TracedLLM, node_span, traces
from backend.llm.base import LLMClient
from backend.rag.answer import answer_question
from backend.rag.retriever import HybridRetriever
from backend.graph.tools import ToolRegistry

System = Literal["single", "multi", "multi_reflect"]


class VajraService:
    def __init__(self, llm: LLMClient, retriever: HybridRetriever, checkpointer=None, tool_store=None) -> None:
        self.llm = TracedLLM(llm)
        self.retriever = retriever
        self.tools = ToolRegistry(retriever, self.llm, tool_store)
        self.graph = build_graph(Deps(self.llm, self.tools), checkpointer)

    # ---------- multi-agent ----------
    def start(self, question: str, *, reflection: bool = True, max_revisions: int = 2,
              auto_approve: bool = False, run_id: str | None = None) -> dict[str, Any]:
        run_id = run_id or f"run-{uuid.uuid4().hex[:10]}"
        traces.start(run_id, "multi_reflect" if reflection else "multi", question)
        init: VajraState = {"run_id": run_id, "question": question, "reflection": reflection,
                            "max_revisions": max_revisions, "auto_approve": auto_approve, "plan": None,
                            "evidence": [], "analysis": None, "calculations": [], "draft": None, "draft_version": 0, "critique": None,
                            "approval": None, "final_answer": None, "status": "planning", "error": None}
        return self._invoke(init, run_id)

    def resume(self, run_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        """Continue a run paused at the approval node (works after a process restart)."""
        snapshot = self.graph.get_state(self._cfg(run_id))
        if not snapshot.next:
            raise ValueError(f"Run {run_id} is not waiting for approval")
        if traces.get(run_id).system == "unknown":
            traces.get(run_id).system = "multi_reflect" if snapshot.values.get("reflection") else "multi"
        return self._invoke(Command(resume=decision), run_id)

    def state(self, run_id: str) -> dict[str, Any]:
        snap = self.graph.get_state(self._cfg(run_id))
        return {"values": snap.values, "next": list(snap.next)}

    def _cfg(self, run_id: str) -> dict:
        # thread_id = checkpoint key. recursion_limit is a hard backstop on total steps.
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 40}

    def _invoke(self, payload: Any, run_id: str) -> dict[str, Any]:
        result = self.graph.invoke(payload, self._cfg(run_id))
        pending = result.get("__interrupt__")
        trace = traces.get(run_id)
        if pending:
            trace.save_json_only()
            return {"run_id": run_id, "status": "awaiting_approval", "approval_request": pending[0].value,
                    "trace": trace.totals()}
        trace.save()
        traces.pop(run_id)
        return {"run_id": run_id, "status": result.get("status"), "final_answer": result.get("final_answer"),
                "draft": result.get("draft"), "evidence": result.get("evidence", []),
                "critique": result.get("critique"), "steps": result.get("steps", []), "trace": trace.totals()}

    # ---------- single-agent baseline ----------
    def single(self, question: str, run_id: str | None = None) -> dict[str, Any]:
        run_id = run_id or f"run-{uuid.uuid4().hex[:10]}"
        trace = traces.start(run_id, "single", question)
        with node_span(run_id, "single_agent"):
            ans = answer_question(question, self.retriever, self.llm, k=5)
        trace.save()
        traces.pop(run_id)
        return {"run_id": run_id, "status": "approved", "final_answer": ans.answer, "draft": ans.answer,
                "evidence": [{"chunk_id": c.chunk_id, "citation": c.citation(), "text": c.text, "score": c.score}
                             for c in ans.chunks],
                "steps": ["single_agent"], "trace": trace.totals()}
