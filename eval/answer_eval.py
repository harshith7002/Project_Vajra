"""Answer eval: generate an answer per question, then score faithfulness and correctness.

Resumable: each finished question is appended to results/answers.jsonl, and a
re-run skips ids already there (CPU runs take a while; a crash loses nothing).

Negative control: for the first N_CONTROL questions the same answer is judged
against the context of a *different* question. A judge that works should mark
most of those claims unsupported; the gap between real and control faithfulness
is how far the judge can be trusted.

    python answer_eval.py            # run / resume
    python answer_eval.py --report   # only rebuild the summary from saved rows
"""
from __future__ import annotations

import json
import statistics
import sys
import time

from common import RESULTS, load_questions

from backend.llm import OllamaClient
from backend.rag.answer import answer_question, format_context
from backend.rag.index import ChunkIndex
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.retriever import HybridRetriever
from judges import judge_correctness, judge_faithfulness

ROWS = RESULTS / "answers.jsonl"
N_CONTROL = 20
NOT_FOUND = "not found in the provided documents"


def faith_score(judgement: dict | None) -> float | None:
    if not judgement or not judgement.get("claims"):
        return None
    claims = judgement["claims"]
    return sum(1 for c in claims if c.get("supported")) / len(claims)


def call_stats(r) -> dict:
    return {"latency_s": round(r.latency_s, 2), "in_tok": r.input_tokens, "out_tok": r.output_tokens,
            "done_reason": r.raw.get("done_reason")}


def run() -> None:
    questions = load_questions()
    RESULTS.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in ROWS.read_text(encoding="utf-8").splitlines()} if ROWS.exists() else set()
    llm = OllamaClient()
    retriever = HybridRetriever(ChunkIndex(llm), reranker=CrossEncoderReranker())
    contexts = {}  # id -> context string, used for the shuffled control
    for i, q in enumerate(questions):
        if q["id"] in done:
            continue
        t0 = time.perf_counter()
        ans = answer_question(q["question"], retriever, llm, k=5)
        context = format_context(ans.chunks)
        contexts[q["id"]] = context
        abstained = NOT_FOUND in ans.answer.lower() or not ans.answer.strip()
        faith, fr = (None, None) if abstained else judge_faithfulness(llm, context, ans.answer)
        corr, cr = judge_correctness(llm, q["question"], q["answer"], ans.answer or "(empty)")
        row = {
            "id": q["id"], "type": q["type"], "question": q["question"], "gold": q["answer"],
            "answer": ans.answer, "abstained": abstained, "citations": [c.citation() for c in ans.chunks],
            "faithfulness": faith_score(faith), "claims": (faith or {}).get("claims"),
            "correctness": (corr or {}).get("verdict"), "correctness_reason": (corr or {}).get("reason"),
            "calls": {"answer": call_stats(ans.llm), "faith": call_stats(fr) if fr else None, "correct": call_stats(cr)},
        }
        if i < N_CONTROL and not abstained:
            # Judge this answer against a context retrieved for an unrelated question.
            other = questions[(i + 25) % len(questions)]
            other_ctx = format_context(retriever.search(other["question"], k=5))
            ctrl, _ = judge_faithfulness(llm, other_ctx, ans.answer)
            row["control_faithfulness"] = faith_score(ctrl)
        with ROWS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        print(f"{q['id']}: corr={row['correctness']} faith={row['faithfulness']} ({time.perf_counter() - t0:.0f}s)", flush=True)


def report() -> None:
    rows = [json.loads(l) for l in ROWS.read_text(encoding="utf-8").splitlines()]
    faith = [r["faithfulness"] for r in rows if r["faithfulness"] is not None]
    ctrl = [r["control_faithfulness"] for r in rows if r.get("control_faithfulness") is not None]
    paired = [(r["faithfulness"], r["control_faithfulness"]) for r in rows
              if r.get("control_faithfulness") is not None and r["faithfulness"] is not None]
    score = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}
    corr = [score[r["correctness"]] for r in rows if r["correctness"] in score]
    calls = [c for r in rows for c in r["calls"].values() if c]
    ans_calls = [r["calls"]["answer"] for r in rows]
    summary = {
        "n_questions": len(rows),
        "abstentions": sum(r["abstained"] for r in rows),
        "judge_parse_failures": sum(1 for r in rows if not r["abstained"] and r["faithfulness"] is None),
        "faithfulness_mean": round(statistics.mean(faith), 3) if faith else None,
        "faithfulness_all_claims_supported": round(sum(1 for f in faith if f == 1.0) / len(faith), 3) if faith else None,
        "control_faithfulness_mean": round(statistics.mean(ctrl), 3) if ctrl else None,
        "control_pairs_where_judge_scored_real_higher": f"{sum(1 for a, b in paired if a > b)}/{len(paired)}",
        "correctness_score_mean": round(statistics.mean(corr), 3) if corr else None,
        "correctness_counts": {v: sum(1 for r in rows if r["correctness"] == v) for v in score},
        "answer_latency_s_median": round(statistics.median(c["latency_s"] for c in ans_calls), 1),
        "answer_output_tokens_median": statistics.median(c["out_tok"] for c in ans_calls),
        "calls_truncated_by_token_limit": sum(1 for c in calls if c.get("done_reason") == "length"),
        "total_llm_calls": len(calls) + len(ctrl),
    }
    (RESULTS / "answers_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    if "--report" not in sys.argv:
        run()
    report()
