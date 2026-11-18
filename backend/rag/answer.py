"""Single-shot RAG answerer: retrieve top-k chunks, ask the local model to answer
from them only, with numbered citations. This is the Phase 1 baseline that the
Phase 2 multi-agent graph will be compared against."""
from __future__ import annotations

from dataclasses import dataclass

from backend.llm.base import ChatMessage, LLMClient, LLMResult
from backend.rag.retriever import HybridRetriever, RetrievedChunk

SYSTEM = (
    "You are VAJRA, an on-premise assistant for industrial maintenance engineers. "
    "Answer ONLY from the numbered context passages. Cite passages like [1] or [2]. "
    "Be concise: one to three sentences. If the context does not contain the answer, "
    "reply exactly: Not found in the provided documents."
)


def format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{i}] ({c.citation()}) {c.text}" for i, c in enumerate(chunks, 1))


@dataclass
class RAGAnswer:
    question: str
    answer: str
    chunks: list[RetrievedChunk]
    llm: LLMResult


def answer_question(question: str, retriever: HybridRetriever, llm: LLMClient, k: int = 5) -> RAGAnswer:
    chunks = retriever.search(question, k=k)
    prompt = f"Context:\n{format_context(chunks)}\n\nQuestion: {question}"
    result = llm.chat([ChatMessage("system", SYSTEM), ChatMessage("user", prompt)])
    return RAGAnswer(question, result.text, chunks, result)
