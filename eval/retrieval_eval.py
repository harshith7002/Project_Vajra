"""Retrieval eval: recall@k and MRR for each retrieval mode.

recall@k  = fraction of a question's gold evidence quotes found in the top-k chunks,
            averaged over questions (multi-hop questions have 2 quotes).
MRR@10    = mean of 1/rank of the first chunk holding any gold quote (0 if none in top 10).
latency   = wall-clock ms per query on this laptop (CPU), median and p95.
"""
from __future__ import annotations

import json
import statistics
import time
from datetime import datetime

from common import RESULTS, evidence_found, load_questions

from backend.llm import OllamaClient
from backend.rag.index import ChunkIndex
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.retriever import MODES, HybridRetriever

KS = (1, 3, 5, 10)


def p95(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]


def main() -> None:
    questions = load_questions()
    index = ChunkIndex(OllamaClient())
    retriever = HybridRetriever(index, reranker=CrossEncoderReranker())
    retriever.search("warm up", k=10)  # load ONNX session / embed model before timing

    summary, per_question = {}, []
    for mode in MODES:
        recalls = {k: [] for k in KS}
        rr, latencies = [], []
        for q in questions:
            t0 = time.perf_counter()
            hits = retriever.search(q["question"], k=max(KS), mode=mode)
            latencies.append((time.perf_counter() - t0) * 1000)
            found_at = []  # rank at which each evidence first appears (None if not in top 10)
            for ev in q["evidence"]:
                rank = next((i for i, h in enumerate(hits, 1) if evidence_found(ev, h.text, h.metadata)), None)
                found_at.append(rank)
            for k in KS:
                recalls[k].append(sum(1 for r in found_at if r and r <= k) / len(found_at))
            first = min((r for r in found_at if r), default=None)
            rr.append(1 / first if first else 0.0)
            per_question.append({"mode": mode, "id": q["id"], "type": q["type"], "evidence_ranks": found_at,
                                 "top3": [h.citation() for h in hits[:3]]})
        summary[mode] = {
            **{f"recall@{k}": round(statistics.mean(recalls[k]), 3) for k in KS},
            "mrr@10": round(statistics.mean(rr), 3),
            "latency_ms_median": round(statistics.median(latencies), 1),
            "latency_ms_p95": round(p95(latencies), 1),
        }
        print(mode, summary[mode])

    RESULTS.mkdir(parents=True, exist_ok=True)
    meta = {"run_at": datetime.now().isoformat(timespec="seconds"), "n_questions": len(questions),
            "n_chunks": len(index), "embed_model": index.llm.embed_model, "reranker": retriever.reranker.model_name,
            "candidates": retriever.candidates, "rrf_k": retriever.rrf_k}
    (RESULTS / "retrieval.json").write_text(json.dumps({"meta": meta, "summary": summary, "per_question": per_question}, indent=2))

    lines = [f"# Retrieval eval ({meta['n_questions']} questions, {meta['n_chunks']} chunks, run {meta['run_at']})", "",
             "| mode | recall@1 | recall@3 | recall@5 | recall@10 | MRR@10 | median ms | p95 ms |", "|---|---|---|---|---|---|---|---|"]
    for mode, s in summary.items():
        lines.append(f"| {mode} | {s['recall@1']} | {s['recall@3']} | {s['recall@5']} | {s['recall@10']} | {s['mrr@10']} | "
                     f"{s['latency_ms_median']} | {s['latency_ms_p95']} |")
    (RESULTS / "retrieval.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
