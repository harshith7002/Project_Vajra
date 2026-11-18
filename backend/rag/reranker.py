"""Cross-encoder re-ranker (ms-marco-MiniLM-L-6-v2, ONNX, ~80 MB, CPU).

Why a second stage: BM25 and the embedding model score query and chunk
*separately* (bi-encoder). A cross-encoder reads the query and the chunk
*together*, so it can see that "who performs the periodic inspection" is
answered by a sentence about "an authorized employee other than the ones
using the procedure". It is too slow to run on every chunk, so it only
re-orders the ~20 candidates the cheap retrievers return.

The model is fetched once by `scripts/fetch_models.py`. At runtime the
HuggingFace hub is forced offline, so loading never opens a network socket.
"""
from __future__ import annotations

import os

from backend.config import settings


class CrossEncoderReranker:
    def __init__(self, model_name: str | None = None) -> None:
        os.environ["HF_HUB_OFFLINE"] = "1"  # air-gapped: load from local cache only
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.model_name = model_name or settings.reranker_model
        self._model = TextCrossEncoder(self.model_name, cache_dir=str(settings.model_cache_dir))

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        return [float(s) for s in self._model.rerank(query, passages, batch_size=16)]
