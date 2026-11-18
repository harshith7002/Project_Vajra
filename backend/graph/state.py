"""Typed graph state shared by every agent node.

LangGraph passes one state object between nodes. Each node returns a *partial*
update, and LangGraph merges it in. Most fields simply get overwritten. Fields
with an `Annotated[..., reducer]` are merged with that reducer instead, which is
how several nodes can append to `evidence` without clobbering each other.

The whole state is checkpointed after every node (SQLite), which is what lets a
run pause at the human approval step and resume later, even in a new process.
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


class Evidence(TypedDict):
    chunk_id: str
    citation: str  # "OSHA_29CFR1910.147_LOTO.pdf p.5"
    text: str
    score: float


class Plan(TypedDict):
    sub_questions: list[str]
    needs_calculation: bool
    rationale: str


class Critique(TypedDict):
    draft_version: int  # which draft this critique is about
    unsupported_claims: list[str]
    verdict: Literal["approve", "revise"]
    feedback: str


class Approval(TypedDict):
    decision: Literal["approve", "reject"]
    reviewer: str
    notes: str


def merge_evidence(old: list[Evidence], new: list[Evidence]) -> list[Evidence]:
    """Append new chunks, de-duplicated by chunk_id, keeping first-seen order (= citation numbers)."""
    seen = {e["chunk_id"] for e in old}
    merged = list(old)
    for e in new:
        if e["chunk_id"] not in seen:
            seen.add(e["chunk_id"])
            merged.append(e)
    return merged


Status = Literal["planning", "working", "awaiting_approval", "approved", "rejected", "failed"]


class VajraState(TypedDict, total=False):
    # inputs
    run_id: str
    question: str
    reflection: bool  # False = plain multi-agent, True = with Critic loop
    max_revisions: int  # N: how many times the Critic may send the draft back
    auto_approve: bool  # eval only: skip the human interrupt

    # working memory
    plan: Plan | None
    evidence: Annotated[list[Evidence], merge_evidence]
    analysis: str | None
    calculations: list[dict[str, Any]]  # exact calculator results, citable as [C1], [C2] ...
    draft: str | None
    draft_version: int  # 1 = first draft, 2 = first revision, ...
    critique: Critique | None
    tool_log: Annotated[list[dict[str, Any]], operator.add]
    steps: Annotated[list[str], operator.add]  # node visit order, for tests and traces

    # outputs
    approval: Approval | None
    final_answer: str | None
    status: Status
    error: str | None
