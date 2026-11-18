"""PDF -> clean, page-attributed sentences.

Steps, in order:
1. Extract text per page with pypdf (keeps the PDF page number for citations).
2. Drop boilerplate: bare page numbers and any line that repeats on >=30% of
   pages (running headers/footers such as "Improving Pumping System Performance").
3. Detect short title-like lines as section headings (best-effort metadata).
4. Re-join wrapped lines, undo end-of-line hyphenation, split into sentences.

The output keeps (sentence, page, section) so every chunk built from it can
cite exactly where its text came from.
"""
from __future__ import annotations

import hashlib
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)

_ABBREVIATIONS = ["e.g.", "i.e.", "etc.", "Fig.", "fig.", "No.", "no.", "U.S.", "vs.", "approx.", "Inc.", "Mr.", "Dr.", "Ref.", "Sec."]
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"“‘])")
_PAGE_NUMBER = re.compile(r"^\s*(page\s+)?\d{1,4}\s*$", re.IGNORECASE)
_LIST_MARKER = re.compile(r"^\(?[0-9ivxA-Z]{1,4}[.)]$")
# Typesetting stamps printed on every page of Federal Register / CFR PDFs.
_PRINT_STAMP = re.compile(r"^(VerDate |Occu\. Safety and Health Admin|29 CFR Ch\. )")


@dataclass
class Sentence:
    text: str
    page: int
    section: str


@dataclass
class LoadedDocument:
    doc_id: str
    filename: str
    num_pages: int
    sentences: list[Sentence]


def _doc_id(path: Path) -> str:
    return "DOC-" + hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _is_heading(line: str) -> bool:
    s = line.strip()
    if not (3 <= len(s) <= 70) or s[-1] in ".,;:-" or not s[0].isupper():
        return False
    words = s.split()
    if len(words) > 10:
        return False
    # Mostly capitalised words ("Section 2: Pumping System Assessment", "LOTO PROCEDURE")
    caps = sum(1 for w in words if w[0].isupper() or not w[0].isalpha())
    return caps / len(words) >= 0.6


def split_sentences(text: str) -> list[str]:
    protected = text
    for i, abbr in enumerate(_ABBREVIATIONS):
        protected = protected.replace(abbr, f"\u0000{i}\u0000")
    parts = _SENTENCE_END.split(protected)
    out: list[str] = []
    pending_marker = ""
    for p in parts:
        for i, abbr in enumerate(_ABBREVIATIONS):
            p = p.replace(f"\u0000{i}\u0000", abbr)
        p = p.strip()
        if not p:
            continue
        # A bare list marker ("1.", "(iv).") is not a sentence: glue it to the next one.
        if _LIST_MARKER.match(p):
            pending_marker = f"{pending_marker} {p}".strip()
            continue
        out.append(f"{pending_marker} {p}".strip() if pending_marker else p)
        pending_marker = ""
    if pending_marker:
        out.append(pending_marker)
    return out


def _join_lines(lines: list[str]) -> str:
    text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if text.endswith("-") and line[:1].islower():
            text = text[:-1] + line  # "temper-" + "ature" -> "temperature"
        elif text:
            text += " " + line
        else:
            text = line
    return re.sub(r"\s+", " ", text)


def load_pdf(path: str | Path) -> LoadedDocument:
    path = Path(path)
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]

    # Boilerplate = lines that recur on many pages (only meaningful for multi-page docs).
    line_counts: Counter[str] = Counter()
    for text in pages:
        line_counts.update({ln.strip() for ln in text.splitlines() if ln.strip()})
    min_repeat = max(3, int(0.3 * len(pages)))
    boilerplate = {ln for ln, c in line_counts.items() if len(pages) >= 5 and c >= min_repeat}

    sentences: list[Sentence] = []
    section = ""
    for page_no, text in enumerate(pages, start=1):
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                for s in split_sentences(_join_lines(buffer)):
                    if len(s) >= 3:
                        sentences.append(Sentence(s, page_no, section))
                buffer.clear()

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped in boilerplate or _PAGE_NUMBER.match(stripped) or _PRINT_STAMP.match(stripped):
                continue
            if _is_heading(stripped) and not (buffer and buffer[-1].rstrip().endswith("-")):
                flush()
                section = stripped
                # Keep the heading text in the stream too so it is searchable.
                sentences.append(Sentence(stripped, page_no, section))
                continue
            buffer.append(stripped)
        flush()

    return LoadedDocument(_doc_id(path), path.name, len(pages), sentences)
