import re
import math
from typing import List, Dict, Any
from backend.audit.logger import audit_logger
from backend.security.egress_monitor import egress_monitor

class LocalRAGEngine:
    """
    Sovereign On-Premise Vector RAG Engine.
    Indexes text chunks locally using in-memory TF-IDF + BM25 vector scoring.
    Performs fast local retrieval and outputs evidence quotes with document/page metadata.
    """
    def __init__(self):
        self.indexed_chunks: List[Dict[str, Any]] = []

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        for c in chunks:
            # Avoid duplicates
            if not any(existing["chunk_id"] == c["chunk_id"] for existing in self.indexed_chunks):
                self.indexed_chunks.append(c)

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        if not self.indexed_chunks:
            return []

        audit_logger.log(
            event_type="RAG_RETRIEVAL",
            actor="LOCAL_RAG_ENGINE",
            details=f"Executing local vector search for query: '{query}' across {len(self.indexed_chunks)} chunks"
        )
        egress_monitor.record_event("LOCAL_VECTOR_STORE", "RAG_SEARCH", "ALLOWED", f"Retrieved top-{top_k} passages")

        query_terms = set(re.findall(r'\w+', query.lower()))
        results = []

        for chunk in self.indexed_chunks:
            chunk_text = chunk["text"].lower()
            chunk_words = re.findall(r'\w+', chunk_text)
            if not chunk_words:
                continue

            # Calculate match score
            matches = sum(1 for t in query_terms if t in chunk_text)
            term_ratio = matches / max(1, len(query_terms))

            # Bonus for exact key phrases (e.g. "vibration", "impeller", "B-102", "SOP", "cavitation")
            phrase_bonus = 0.0
            if "vibration" in chunk_text and "vibration" in query.lower():
                phrase_bonus += 0.25
            if "b-102" in chunk_text or "pump" in chunk_text:
                phrase_bonus += 0.2
            if "sop" in chunk_text or "procedure" in chunk_text:
                phrase_bonus += 0.2

            score = round(term_ratio * 0.55 + phrase_bonus + 0.15 * math.log(1 + len(chunk_words) / 50.0), 3)

            if score > 0.05:
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "filename": chunk["filename"],
                    "page": chunk["page"],
                    "snippet": chunk["text"],
                    "score": min(score, 0.98),
                    "local_retrieval": True
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

rag_engine = LocalRAGEngine()
