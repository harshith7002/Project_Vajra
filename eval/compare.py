"""Phase 3: single-agent vs multi-agent vs multi-agent + reflection on the 50-question set.

Per question and system we record the answer, the full trace totals (latency,
tokens, tok/s, retries, cost), then judge faithfulness (against exactly the
evidence + calculator results that system saw) and correctness (against gold).
Judge calls are NOT counted in system cost.

Rows are appended to results/compare.jsonl and skipped on re-run (resumable).
Questions are processed one at a time across all three systems, so a partial
run is still a balanced comparison.

    python compare.py [--limit N] [--report]
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

from common import RESULTS, load_questions

from backend.llm import OllamaClient
from backend.graph.agents import numbered_calcs
from backend.graph.service import VajraService
from backend.rag.index import ChunkIndex
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.retriever import HybridRetriever
from judges import judge_correctness, judge_faithfulness

ROWS = RESULTS / "compare.jsonl"
SYSTEMS = ("single", "multi", "multi_reflect")
NOT_FOUND = "not found in the provided documents"
MAX_REVISIONS = 2


def context_of(out: dict) -> str:
    ev = "\n\n".join(f"[{i}] ({e['citation']}) {e['text']}" for i, e in enumerate(out["evidence"], 1))
    return ev + "\n\nCALCULATOR RESULTS (exact):\n" + numbered_calcs(out.get("calculations") or [])


def run(limit: int | None) -> None:
    questions = load_questions()[:limit]
    RESULTS.mkdir(parents=True, exist_ok=True)
    done = set()
    if ROWS.exists():
        done = {(r["id"], r["system"]) for r in map(json.loads, ROWS.read_text(encoding="utf-8").splitlines())}
    llm = OllamaClient()
    judge = OllamaClient()  # separate, untraced client
    svc = VajraService(llm, HybridRetriever(ChunkIndex(llm), reranker=CrossEncoderReranker()))
    for q in questions:
        for system in SYSTEMS:
            if (q["id"], system) in done:
                continue
            t0 = time.perf_counter()
            try:
                if system == "single":
                    out = svc.single(q["question"], run_id=f"cmp-{system}-{q['id']}")
                else:
                    out = svc.start(q["question"], reflection=(system == "multi_reflect"), max_revisions=MAX_REVISIONS,
                                    auto_approve=True, run_id=f"cmp-{system}-{q['id']}-{int(time.time())}")
                    out["calculations"] = svc.state(out["run_id"])["values"].get("calculations", [])
                error = None
            except Exception as e:  # a crash is a result too; record it and move on
                out, error = {"final_answer": "", "evidence": [], "trace": {}, "steps": []}, f"{type(e).__name__}: {e}"
            answer = out.get("final_answer") or out.get("draft") or ""
            abstained = not answer.strip() or NOT_FOUND in answer.lower()
            faith = None
            if not abstained:
                fj, _ = judge_faithfulness(judge, context_of(out), answer)
                if fj and fj.get("claims"):
                    faith = sum(1 for c in fj["claims"] if c.get("supported")) / len(fj["claims"])
            cj, _ = judge_correctness(judge, q["question"], q["answer"], answer or "(empty)")
            row = {"id": q["id"], "type": q["type"], "system": system, "answer": answer, "abstained": abstained,
                   "error": error, "faithfulness": faith, "correctness": (cj or {}).get("verdict"),
                   "revisions": max(0, out.get("steps", []).count("writer") - 1),
                   "critic_final_verdict": (out.get("critique") or {}).get("verdict"),
                   "trace": out.get("trace", {})}
            with ROWS.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{q['id']:9s} {system:13s} corr={row['correctness']} faith={faith} "
                  f"sys={row['trace'].get('wall_s')}s total={time.perf_counter() - t0:.0f}s", flush=True)


def report() -> dict:
    rows = [json.loads(l) for l in ROWS.read_text(encoding="utf-8").splitlines()]
    pts = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}
    # Compare only questions every system finished, so the averages are over the same set.
    ids = set.intersection(*({r["id"] for r in rows if r["system"] == s} for s in SYSTEMS))
    price_as = os.environ.get("VAJRA_PRICE_AS")
    prices = json.loads((RESULTS.parent.parent / "config" / "prices.json").read_text())["models"]
    out: dict = {"n_questions": len(ids), "systems": {}}
    for s in SYSTEMS:
        rs = [r for r in rows if r["system"] == s and r["id"] in ids]
        tr = [r["trace"] for r in rs if r["trace"]]
        faith = [r["faithfulness"] for r in rs if r["faithfulness"] is not None]
        corr = [pts[r["correctness"]] for r in rs if r["correctness"] in pts]
        m = {
            "correctness": round(statistics.mean(corr), 3) if corr else None,
            "fully_correct": sum(r["correctness"] == "correct" for r in rs),
            "faithfulness": round(statistics.mean(faith), 3) if faith else None,
            "abstentions": sum(r["abstained"] for r in rs),
            "errors": sum(1 for r in rs if r["error"]),
            "latency_s_median": round(statistics.median(t["wall_s"] for t in tr), 1),
            "latency_s_p95": round(sorted(t["wall_s"] for t in tr)[int(0.95 * (len(tr) - 1))], 1),
            "llm_calls_mean": round(statistics.mean(t["llm_calls"] for t in tr), 2),
            "input_tokens_mean": round(statistics.mean(t["input_tokens"] for t in tr)),
            "output_tokens_mean": round(statistics.mean(t["output_tokens"] for t in tr)),
            "decode_tok_s_mean": round(statistics.mean(t["decode_tokens_per_s"] for t in tr if t.get("decode_tokens_per_s")), 2),
            "retries_total": sum(t["retries"] for t in tr),
            "cost_usd_per_request": round(statistics.mean(t["cost_usd"] for t in tr), 6),
            "revisions_mean": round(statistics.mean(r["revisions"] for r in rs), 2),
        }
        if price_as and price_as in prices:
            p = prices[price_as]
            m[f"cost_usd_per_request_at_{price_as}"] = round(
                (m["input_tokens_mean"] * p["input_per_1m"] + m["output_tokens_mean"] * p["output_per_1m"]) / 1e6, 6)
        out["systems"][s] = m
    (RESULTS / "compare_summary.json").write_text(json.dumps(out, indent=2))

    cols = ["correctness", "fully_correct", "faithfulness", "abstentions", "latency_s_median", "latency_s_p95",
            "llm_calls_mean", "input_tokens_mean", "output_tokens_mean", "decode_tok_s_mean", "cost_usd_per_request"]
    lines = [f"# Single vs multi-agent vs multi-agent + reflection ({out['n_questions']} questions, model "
             f"{OllamaClient().model}, CPU)", "", "| system | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for s, m in out["systems"].items():
        lines.append(f"| {s} | " + " | ".join(str(m[c]) for c in cols) + " |")
    (RESULTS / "compare.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return out


if __name__ == "__main__":
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if "--report" not in sys.argv:
        run(limit)
    report()
