"""One-time model provisioning (the ONLY step that needs internet).

On an air-gapped site you run this on a connected staging machine, then copy
the `models/` folder and Ollama's model store across. After that the runtime
never needs the network.

    python scripts/fetch_models.py
    ollama pull nomic-embed-text && ollama pull qwen3-vl:2b
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastembed.rerank.cross_encoder import TextCrossEncoder  # noqa: E402

from backend.config import settings  # noqa: E402

if __name__ == "__main__":
    settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
    TextCrossEncoder(settings.reranker_model, cache_dir=str(settings.model_cache_dir))
    print(f"Cached {settings.reranker_model} in {settings.model_cache_dir}")
