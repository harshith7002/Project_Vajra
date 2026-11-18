"""Semantic chunking: cut where the topic changes, not every N characters.

How it works (the "embedding breakpoint" method):
1. Embed each sentence together with its neighbours (a 3-sentence window), so a
   single short sentence does not produce a noisy vector.
2. Measure cosine distance between consecutive windows. A big jump means the
   text moved to a new topic.
3. Cut wherever the distance is above this document's `breakpoint_percentile`
   (default 85th percentile), as long as the chunk already has `min_chars`.
4. Hard limits: never exceed `max_chars` (keeps chunks inside the embedding
   model's context and the LLM prompt budget).

Fixed-size chunking is kept as `fixed_size_chunks` so the two can be compared.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from backend.rag.pdf_loader import LoadedDocument, Sentence

Embedder = Callable[[list[str]], list[list[float]]]


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    filename: str
    chunk_index: int
    page_start: int
    page_end: int
    section: str
    text: str

    @property
    def metadata(self) -> dict:
        d = asdict(self)
        d.pop("text")
        d["n_chars"] = len(self.text)
        return d


def _make_chunk(doc: LoadedDocument, index: int, sents: list[Sentence]) -> Chunk:
    text = " ".join(s.text for s in sents)
    # Content-addressed id: re-ingesting the same file yields the same ids (idempotent upsert).
    digest = hashlib.sha1(f"{doc.doc_id}|{text}".encode("utf-8")).hexdigest()[:12]
    return Chunk(
        chunk_id=f"{doc.doc_id}-{digest}",
        doc_id=doc.doc_id,
        filename=doc.filename,
        chunk_index=index,
        page_start=sents[0].page,
        page_end=sents[-1].page,
        section=next((s.section for s in sents if s.section), ""),
        text=text,
    )


def _cosine_distances(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    unit = vectors / np.clip(norms, 1e-12, None)
    return 1.0 - np.sum(unit[:-1] * unit[1:], axis=1)


def semantic_chunks(
    doc: LoadedDocument,
    embed: Embedder,
    *,
    window: int = 1,
    breakpoint_percentile: float = 85.0,
    min_chars: int = 350,
    max_chars: int = 1400,
) -> list[Chunk]:
    sents = doc.sentences
    if not sents:
        return []
    if len(sents) < 3:
        return [_make_chunk(doc, 0, sents)]

    windows = [
        " ".join(s.text for s in sents[max(0, i - window) : i + window + 1]) for i in range(len(sents))
    ]
    # nomic-embed-text expects a task prefix; "clustering:" is the one meant for topic similarity.
    vectors = np.asarray(embed([f"clustering: {w}" for w in windows]), dtype=np.float32)
    distances = _cosine_distances(vectors)  # distances[i] = gap between sentence i and i+1
    threshold = float(np.percentile(distances, breakpoint_percentile))

    groups: list[list[Sentence]] = []
    current: list[Sentence] = []
    size = 0
    for i, s in enumerate(sents):
        if current and size + len(s.text) + 1 > max_chars:
            groups.append(current)
            current, size = [], 0
        current.append(s)
        size += len(s.text) + 1
        is_topic_shift = i < len(distances) and distances[i] > threshold
        if is_topic_shift and size >= min_chars:
            groups.append(current)
            current, size = [], 0
    if current:
        # Fold a tiny tail into the previous chunk instead of leaving a fragment.
        prev_size = sum(len(s.text) + 1 for s in groups[-1]) if groups else 0
        if groups and size < min_chars // 2 and prev_size + size <= max_chars:
            groups[-1].extend(current)
        else:
            groups.append(current)
    return [_make_chunk(doc, i, g) for i, g in enumerate(groups)]


def fixed_size_chunks(doc: LoadedDocument, *, max_chars: int = 1000) -> list[Chunk]:
    """Baseline: pack whole sentences until max_chars, ignoring topic."""
    chunks: list[Chunk] = []
    current: list[Sentence] = []
    size = 0
    for s in doc.sentences:
        if current and size + len(s.text) + 1 > max_chars:
            chunks.append(_make_chunk(doc, len(chunks), current))
            current, size = [], 0
        current.append(s)
        size += len(s.text) + 1
    if current:
        chunks.append(_make_chunk(doc, len(chunks), current))
    return chunks
