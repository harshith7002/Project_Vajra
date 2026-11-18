"""Persistent chunk index: Chroma (dense vectors) + BM25 (sparse keywords).

Chroma stores text, metadata and the nomic-embed-text vector for every chunk on
local disk. BM25 is rebuilt in memory from the same chunks at load time; at a
few hundred chunks that takes milliseconds, and it means there is only one
source of truth on disk.

Ingestion is idempotent: a document whose doc_id (hash of the file bytes) is
already indexed is skipped, and chunk ids are content hashes, so re-running
ingest never duplicates chunks.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

# Chroma ships anonymous usage telemetry that would phone home. Off, always.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402
from chromadb.config import Settings as ChromaSettings  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402

from backend.audit.logger import audit_logger  # noqa: E402
from backend.config import settings  # noqa: E402
from backend.llm.base import LLMClient  # noqa: E402
from backend.rag.chunker import Chunk, semantic_chunks  # noqa: E402
from backend.rag.pdf_loader import load_pdf  # noqa: E402

COLLECTION = "vajra_chunks"
_TOKEN = re.compile(r"[a-z0-9]+(?:[-./][a-z0-9]+)*")
_STOPWORDS = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the this to was were which with what when "
    "how does do should must shall can may will".split()
)


def tokenize(text: str) -> list[str]:
    """Keeps plant tags like 'hv-104' and clause ids like '1910.147' as single tokens."""
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]


@dataclass
class IngestReport:
    files_seen: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    chunks_added: int = 0
    seconds: float = 0.0
    per_file: list[dict] = field(default_factory=list)


class ChunkIndex:
    def __init__(self, llm: LLMClient, index_dir: Path | None = None) -> None:
        self.llm = llm
        path = Path(index_dir or settings.index_dir) / "chroma"
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path), settings=ChromaSettings(anonymized_telemetry=False))
        self.collection = self._client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        self._load_sparse()

    # ---------- ingestion ----------
    def has_document(self, doc_id: str) -> bool:
        return bool(self.collection.get(where={"doc_id": doc_id}, limit=1)["ids"])

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        # nomic-embed-text is trained with task prefixes: documents get "search_document:".
        vectors = self.llm.embed([f"search_document: {c.text}" for c in chunks])
        self.collection.upsert(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[c.metadata for c in chunks],
            embeddings=vectors,
        )

    def ingest_dir(self, corpus_dir: Path | None = None) -> IngestReport:
        report = IngestReport()
        start = time.perf_counter()
        for pdf in sorted(Path(corpus_dir or settings.corpus_dir).glob("*.pdf")):
            report.files_seen += 1
            t0 = time.perf_counter()
            doc = load_pdf(pdf)
            if self.has_document(doc.doc_id):
                report.files_skipped += 1
                continue
            chunks = semantic_chunks(doc, self.llm.embed)
            self.add_chunks(chunks)
            report.files_indexed += 1
            report.chunks_added += len(chunks)
            report.per_file.append(
                {"file": pdf.name, "pages": doc.num_pages, "chunks": len(chunks), "seconds": round(time.perf_counter() - t0, 1)}
            )
            audit_logger.log("DOCUMENT_INDEXED", "LOCAL_INDEXER", f"Indexed {pdf.name}: {len(chunks)} semantic chunks", doc_id=doc.doc_id)
        report.seconds = round(time.perf_counter() - start, 1)
        self._load_sparse()
        return report

    # ---------- retrieval primitives ----------
    def _load_sparse(self) -> None:
        data = self.collection.get(include=["documents", "metadatas"])
        self.ids: list[str] = data["ids"]
        self.texts: dict[str, str] = dict(zip(data["ids"], data["documents"] or []))
        self.metas: dict[str, dict] = dict(zip(data["ids"], data["metadatas"] or []))
        self._bm25 = BM25Okapi([tokenize(self.texts[i]) for i in self.ids]) if self.ids else None

    def __len__(self) -> int:
        return len(self.ids)

    def bm25_search(self, query: str, n: int) -> list[tuple[str, float]]:
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.ids, scores), key=lambda x: x[1], reverse=True)
        return [(cid, float(s)) for cid, s in ranked[:n] if s > 0]

    def vector_search(self, query: str, n: int) -> list[tuple[str, float]]:
        if not self.ids:
            return []
        qvec = self.llm.embed([f"search_query: {query}"])[0]
        res = self.collection.query(query_embeddings=[qvec], n_results=min(n, len(self.ids)))
        # Chroma returns cosine *distance*; convert to similarity for readability.
        return [(cid, 1.0 - float(d)) for cid, d in zip(res["ids"][0], res["distances"][0])]
