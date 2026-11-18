"""Fast unit tests for Phase 1 (no Ollama, no network, no model files)."""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from backend.rag.chunker import fixed_size_chunks, semantic_chunks
from backend.rag.index import tokenize
from backend.rag.pdf_loader import LoadedDocument, Sentence, split_sentences
from backend.rag.retriever import reciprocal_rank_fusion
from backend.security.egress_guard import EgressBlocked, check_url


def test_tokenize_keeps_plant_tags_and_clause_ids():
    toks = tokenize("Lock out Valve HV-104 per 1910.147(c)(4) and B-102-BRG")
    assert "hv-104" in toks and "1910.147" in toks and "b-102-brg" in toks
    assert "and" not in toks  # stopword removed


def test_sentence_split_respects_abbreviations_and_list_markers():
    s = split_sentences("Use a VFD, e.g. on pump B. It saves energy. 1. Obtain the note. 2. Verify LOTO.")
    assert s == ["Use a VFD, e.g. on pump B.", "It saves energy.", "1. Obtain the note.", "2. Verify LOTO."]


def test_rrf_rewards_agreement_between_retrievers():
    fused = dict(reciprocal_rank_fusion([["a", "b", "c"], ["b", "d", "a"]], k=60))
    # 'b' is ranked 2nd and 1st -> beats 'a' (1st and 3rd); both beat single-list items.
    assert fused["b"] > fused["a"] > fused["c"]
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)


def _doc(texts: list[str]) -> LoadedDocument:
    return LoadedDocument("DOC-test", "t.pdf", 2, [Sentence(t, 1 if i < len(texts) // 2 else 2, "") for i, t in enumerate(texts)])


def _topic_embedder(texts: list[str]) -> list[list[float]]:
    # Deterministic fake: vectors point one way for 'pump' text and another for 'lock' text.
    return [[1.0, 0.0] if "pump" in t else [0.0, 1.0] for t in texts]


def test_semantic_chunker_cuts_at_topic_shift_and_keeps_pages():
    pump = [f"The pump sentence number {i} talks about impellers and flow rate." for i in range(8)]
    lock = [f"The lock sentence number {i} talks about tags and isolation." for i in range(8)]
    chunks = semantic_chunks(_doc(pump + lock), _topic_embedder, min_chars=100, max_chars=2000)
    assert len(chunks) == 2
    assert all("pump" in c.text for c in chunks[:1]) and "lock" in chunks[1].text and "pump" not in chunks[1].text
    assert chunks[0].page_start == 1 and chunks[1].page_end == 2


def test_chunker_respects_max_chars_and_ids_are_stable():
    sents = [f"Sentence {i} " + "x" * 80 for i in range(30)]
    a = fixed_size_chunks(_doc(sents), max_chars=400)
    b = fixed_size_chunks(_doc(sents), max_chars=400)
    assert all(len(c.text) <= 400 for c in a)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]  # idempotent re-ingest
    expected = hashlib.sha1(f"DOC-test|{a[0].text}".encode()).hexdigest()[:12]
    assert a[0].chunk_id.endswith(expected)


def test_egress_guard_blocks_non_allowlisted_hosts():
    check_url("http://127.0.0.1:11434/api/chat", "TEST")  # allowed, no exception
    with pytest.raises(EgressBlocked):
        check_url("https://generativelanguage.googleapis.com/v1/models", "TEST")
    with pytest.raises(EgressBlocked):
        check_url("http://example.com", "TEST", allowlist=("127.0.0.1",))
