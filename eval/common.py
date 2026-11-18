"""Shared helpers for the eval scripts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

QUESTIONS = ROOT / "eval" / "questions.jsonl"
RESULTS = ROOT / "eval" / "results"


def norm(text: str) -> str:
    """Compare text ignoring case, punctuation, hyphenation and whitespace."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def load_questions() -> list[dict]:
    return [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]


def evidence_found(evidence: dict, chunk_text: str, chunk_meta: dict) -> bool:
    """A retrieved chunk 'contains' a gold evidence if it is from the right file and holds the quote."""
    return chunk_meta["filename"] == evidence["file"] and norm(evidence["quote"]) in norm(chunk_text)
