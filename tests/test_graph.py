"""Phase 2 tests with a scripted fake LLM (no Ollama, deterministic, ~seconds).

Covers: graph routing, reflection-loop termination, pause/resume across a
"process restart", typed tool validation, and idempotent tool calls.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

import backend.graph.tracing as tracing
from backend.graph.agents import route
from backend.graph.service import VajraService
from backend.graph.tools import ToolRegistry, ToolResultStore, safe_eval
from backend.llm.base import LLMResult

CHUNKS = [
    ("c1", "SOP_Pump_Maintenance_2025.pdf", "Vibration above 7.0 mm/s RMS requires a Category 2 Emergency Shutdown."),
    ("c2", "Pump_Inspection_Report_07.pdf", "Vibration level measured at 7.8 mm/s RMS on drive-end bearing housing."),
]


class FakeRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, k: int = 5, mode: str = "hybrid_rerank"):
        self.calls += 1
        return [SimpleNamespace(chunk_id=cid, text=text, score=1.0, metadata={"filename": f},
                                citation=lambda f=f: f"{f} p.1") for cid, f, text in CHUNKS[:k]]


class FakeLLM:
    """Answers by looking at which agent's system prompt it received."""
    provider, model = "fake", "fake-model"

    def __init__(self, critic_always_rejects: bool = False) -> None:
        self.critic_always_rejects = critic_always_rejects
        self.calls: list[str] = []

    def embed(self, texts):
        return [[0.0] for _ in texts]

    def chat(self, messages, json_schema=None, **kw) -> LLMResult:
        system = messages[0].content
        if "plan research" in system:
            agent, out = "planner", {"sub_questions": ["SOP vibration threshold"], "needs_calculation": True, "rationale": "r"}
        elif "Retriever agent" in system:
            agent, out = "retriever", {"thought": "enough", "action": "finish", "args": {}, "final": ""}
        elif "Analyst agent" in system:
            agent = "analyst"
            done = "Observation" in messages[-1].content
            out = ({"thought": "t", "action": "finish", "args": {}, "final": "Exceeds by 0.8 mm/s [1][2]"} if done else
                   {"thought": "diff", "action": "calculator", "args": {"expression": "7.8 - 7.0"}, "final": ""})
        elif "Critic agent" in system:
            agent = "critic"
            out = {"claims": [{"claim": "x", "supported": not self.critic_always_rejects, "evidence_ids": [1]}],
                   "feedback": "remove x"}
        elif "Writer agent" in system:
            agent, out = "writer", "It exceeds the 7.0 mm/s limit by 0.8 mm/s [1][2]."
        else:
            agent, out = "other", "answer [1]"
        self.calls.append(agent)
        text = out if isinstance(out, str) else json.dumps(out)
        return LLMResult(text=text, model=self.model, provider="fake", input_tokens=100, output_tokens=20, latency_s=0.01)


@pytest.fixture(autouse=True)
def _tmp_traces(tmp_path, monkeypatch):
    monkeypatch.setattr(tracing, "TRACE_DIR", tmp_path / "traces")


def make_service(tmp_path, llm=None, db="ckpt.sqlite"):
    import sqlite3
    saver = SqliteSaver(sqlite3.connect(str(tmp_path / db), check_same_thread=False))
    return VajraService(llm or FakeLLM(), FakeRetriever(), checkpointer=saver,
                        tool_store=ToolResultStore(tmp_path / "tools.sqlite"))


# ---------------- routing ----------------
BASE = {"plan": {"sub_questions": [], "needs_calculation": False, "rationale": ""}, "evidence": [{"chunk_id": "c1"}],
        "analysis": "notes", "draft": "d", "draft_version": 1, "reflection": True, "max_revisions": 2, "critique": None}


@pytest.mark.parametrize("override, expected", [
    ({"plan": None}, "supervisor"),
    ({"evidence": []}, "retriever"),
    ({"analysis": None}, "analyst"),
    ({"draft": None}, "writer"),
    ({}, "critic"),  # draft v1 not yet critiqued
    ({"critique": {"draft_version": 1, "verdict": "revise"}}, "writer"),
    ({"critique": {"draft_version": 1, "verdict": "approve"}}, "approval"),
    ({"draft_version": 3, "critique": {"draft_version": 3, "verdict": "revise"}}, "approval"),  # N=2 revisions used up
    ({"reflection": False}, "approval"),
    ({"status": "failed"}, "__end__"),
])
def test_route(override, expected):
    assert route({**BASE, **override}) == expected


# ---------------- end-to-end graph behaviour ----------------
def test_multi_agent_without_reflection_skips_critic(tmp_path):
    svc = make_service(tmp_path)
    out = svc.start("How far over the limit is B-102?", reflection=False, auto_approve=True)
    assert out["status"] == "approved"
    assert "critic" not in out["steps"]
    assert [s for s in out["steps"] if s != "supervisor"] == ["retriever", "analyst", "writer", "approval"]
    assert out["trace"]["llm_calls"] > 0 and out["trace"]["tool_calls"] > 0


@pytest.mark.parametrize("max_revisions", [0, 1, 3])
def test_reflection_loop_terminates_after_n_revisions(tmp_path, max_revisions):
    llm = FakeLLM(critic_always_rejects=True)
    out = make_service(tmp_path, llm).start("q", reflection=True, max_revisions=max_revisions, auto_approve=True)
    assert out["status"] == "approved"  # still reaches the human gate, with the critique attached
    assert out["steps"].count("writer") == max_revisions + 1
    assert out["steps"].count("critic") == max_revisions + 1
    assert out["critique"]["verdict"] == "revise"


def test_reflection_stops_early_when_critic_approves(tmp_path):
    out = make_service(tmp_path).start("q", reflection=True, max_revisions=3, auto_approve=True)
    assert out["steps"].count("writer") == 1 and out["steps"].count("critic") == 1


def test_pause_for_approval_and_resume_in_new_process(tmp_path):
    first = make_service(tmp_path)
    paused = first.start("q", reflection=True)
    assert paused["status"] == "awaiting_approval"
    assert paused["approval_request"]["draft"]
    run_id = paused["run_id"]
    tracing.traces.pop(run_id)  # simulate the process dying: in-memory trace gone

    second = make_service(tmp_path)  # fresh graph, same SQLite checkpoint file
    done = second.resume(run_id, {"decision": "approve", "reviewer": "Lead", "notes": "ok"})
    assert done["status"] == "approved" and done["final_answer"]
    assert done["trace"]["llm_calls"] >= paused["trace"]["llm_calls"]  # trace continued, not restarted
    with pytest.raises(ValueError):
        second.resume(run_id, {"decision": "approve"})  # already finished


def test_reject_produces_no_final_answer(tmp_path):
    svc = make_service(tmp_path)
    run_id = svc.start("q", reflection=False)["run_id"]
    out = svc.resume(run_id, {"decision": "reject", "reviewer": "Lead", "notes": "wrong pump"})
    assert out["status"] == "rejected" and out["final_answer"] is None


# ---------------- tools ----------------
def registry(tmp_path) -> tuple[ToolRegistry, FakeRetriever]:
    r = FakeRetriever()
    return ToolRegistry(r, FakeLLM(), ToolResultStore(tmp_path / "t.sqlite")), r


@pytest.mark.parametrize("name, args, fragment", [
    ("search_documents", {"query": "ab"}, "query"),  # too short
    ("search_documents", {"query": "valid query", "k": 50}, "k"),  # out of range
    ("calculator", {}, "expression"),  # missing
    ("extract_fields", {"fields": ["  "]}, "fields"),  # empty after strip
    ("delete_everything", {}, "Unknown tool"),
])
def test_tool_schema_validation_rejects_bad_calls(tmp_path, name, args, fragment):
    reg, retr = registry(tmp_path)
    out = reg.call(name, args, run_id="r1")
    assert not out.ok and fragment in out.result
    assert retr.calls == 0  # nothing executed


def test_calculator_is_safe():
    assert safe_eval("(7.8 - 7.0) / 7.0 * 100") == pytest.approx(11.428571, rel=1e-5)
    for bad in ("__import__('os').system('x')", "open('f')", "2 ** 1000", "a + 1"):
        with pytest.raises(ValueError):
            safe_eval(bad)


def test_tool_calls_are_idempotent_per_run(tmp_path):
    reg, retr = registry(tmp_path)
    a = reg.call("search_documents", {"query": "vibration limit", "k": 2}, run_id="r1")
    b = reg.call("search_documents", {"k": 2, "query": "vibration limit"}, run_id="r1")  # same call, other key order
    assert a.ok and b.ok and not a.cached and b.cached and a.result == b.result
    assert retr.calls == 1
    reg.call("search_documents", {"query": "vibration limit", "k": 2}, run_id="r2")  # other run: executes
    assert retr.calls == 2
    # Survives a restart: a new registry on the same store file still hits the cache.
    reg2 = ToolRegistry(retr, FakeLLM(), ToolResultStore(tmp_path / "t.sqlite"))
    assert reg2.call("search_documents", {"query": "vibration limit", "k": 2}, run_id="r1").cached
