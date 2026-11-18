"""Hybrid retrieval: BM25 + vectors, fused with Reciprocal Rank Fusion, then re-ranked.

Modes (all used by the eval so each stage's contribution is measured):
  bm25           keyword only
  vector         embeddings only
  hybrid         RRF(bm25, vector)
  hybrid_rerank  RRF candidates re-ordered by the cross-encoder (default)

RRF in one line: score(chunk) = sum over retrievers of 1 / (k + rank).
It only uses ranks, so it does not care that BM25 scores (0..~30) and cosine
similarities (0..1) live on different scales. k=60 is the value from the
original paper (Cormack et al., 2009); it damps the influence of rank 1 vs 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from backend.rag.index import ChunkIndex

Mode = Literal["bm25", "vector", "hybrid", "hybrid_rerank"]
MODES: tuple[Mode, ...] = ("bm25", "vector", "hybrid", "hybrid_rerank")


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    score: float
    ranks: dict[str, int] = field(default_factory=dict)  # rank in each stage, for debugging/traces

    def citation(self) -> str:
        m = self.metadata
        pages = f"p.{m['page_start']}" if m["page_start"] == m["page_end"] else f"pp.{m['page_start']}-{m['page_end']}"
        return f"{m['filename']} {pages}"


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridRetriever:
    def __init__(self, index: ChunkIndex, reranker=None, candidates: int = 20, rrf_k: int = 60) -> None:
        self.index = index
        self.reranker = reranker
        self.candidates = candidates
        self.rrf_k = rrf_k

    def _wrap(self, cid: str, score: float, ranks: dict[str, int]) -> RetrievedChunk:
        return RetrievedChunk(cid, self.index.texts[cid], self.index.metas[cid], score, ranks)

    def search(self, query: str, k: int = 5, mode: Mode = "hybrid_rerank") -> list[RetrievedChunk]:
        if mode == "bm25":
            return [self._wrap(c, s, {"bm25": r}) for r, (c, s) in enumerate(self.index.bm25_search(query, k), 1)]
        if mode == "vector":
            return [self._wrap(c, s, {"vector": r}) for r, (c, s) in enumerate(self.index.vector_search(query, k), 1)]

        bm25 = [c for c, _ in self.index.bm25_search(query, self.candidates)]
        vec = [c for c, _ in self.index.vector_search(query, self.candidates)]
        fused = reciprocal_rank_fusion([bm25, vec], k=self.rrf_k)

        def ranks_for(cid: str, fused_rank: int) -> dict[str, int]:
            r = {"rrf": fused_rank}
            if cid in bm25:
                r["bm25"] = bm25.index(cid) + 1
            if cid in vec:
                r["vector"] = vec.index(cid) + 1
            return r

        if mode == "hybrid" or self.reranker is None:
            return [self._wrap(c, s, ranks_for(c, i)) for i, (c, s) in enumerate(fused[:k], 1)]

        pool = fused[: self.candidates]
        scores = self.reranker.score(query, [self.index.texts[c] for c, _ in pool])
        reranked = sorted(zip(pool, scores), key=lambda x: x[1], reverse=True)
        out = []
        for new_rank, ((cid, _), s) in enumerate(reranked[:k], 1):
            r = ranks_for(cid, [c for c, _ in pool].index(cid) + 1)
            r["rerank"] = new_rank
            out.append(self._wrap(cid, s, r))
        return out
