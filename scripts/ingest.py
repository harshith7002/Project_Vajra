"""Build (or update) the local index from data/corpus/*.pdf. Safe to re-run."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.llm import OllamaClient  # noqa: E402
from backend.rag.index import ChunkIndex  # noqa: E402

if __name__ == "__main__":
    index = ChunkIndex(OllamaClient())
    report = index.ingest_dir()
    print(json.dumps(report.__dict__, indent=2))
    print(f"Index now holds {len(index)} chunks")
