"""Sanity-check the eval set against the real documents and the built index.

For every gold evidence quote:
  * it must appear on the stated page of the source PDF (catches typos in the set), and
  * at least one indexed chunk must contain it whole (if a chunk boundary split the
    quote, recall@k could never reach 1 for that question, which would be unfair).
"""
from __future__ import annotations

from collections import defaultdict

from common import ROOT, evidence_found, load_questions, norm

from backend.llm import OllamaClient
from backend.rag.index import ChunkIndex
from backend.rag.pdf_loader import load_pdf

if __name__ == "__main__":
    questions = load_questions()
    pages: dict[str, dict[int, str]] = defaultdict(dict)
    for q in questions:
        for ev in q["evidence"]:
            if ev["file"] not in pages:
                doc = load_pdf(ROOT / "data" / "corpus" / ev["file"])
                for s in doc.sentences:
                    pages[ev["file"]][s.page] = pages[ev["file"]].get(s.page, "") + " " + s.text
    index = ChunkIndex(OllamaClient())
    problems = 0
    for q in questions:
        for ev in q["evidence"]:
            on_page = norm(ev["quote"]) in norm(pages[ev["file"]].get(ev["page"], ""))
            in_chunk = any(evidence_found(ev, index.texts[c], index.metas[c]) for c in index.ids)
            if not (on_page and in_chunk):
                problems += 1
                print(f"{q['id']}: on_page={on_page} in_one_chunk={in_chunk} :: {ev['quote']}")
    n_ev = sum(len(q["evidence"]) for q in questions)
    print(f"{len(questions)} questions, {n_ev} evidence quotes, {problems} problems")
