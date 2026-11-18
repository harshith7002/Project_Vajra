"""Central settings for the rebuilt VAJRA pipeline.

All values come from environment variables so the same code runs on a laptop,
inside docker-compose, or in a test with monkeypatched env. Nothing here talks
to the network.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    # Local model runtime
    ollama_url: str = field(default_factory=lambda: _env("VAJRA_OLLAMA_URL", "http://127.0.0.1:11434"))
    chat_model: str = field(default_factory=lambda: _env("VAJRA_CHAT_MODEL", "qwen3-vl:2b"))
    embed_model: str = field(default_factory=lambda: _env("VAJRA_EMBED_MODEL", "nomic-embed-text"))
    llm_timeout_s: float = field(default_factory=lambda: float(_env("VAJRA_LLM_TIMEOUT_S", "180")))
    llm_max_tokens: int = field(default_factory=lambda: int(_env("VAJRA_LLM_MAX_TOKENS", "1536")))

    # Storage
    corpus_dir: Path = field(default_factory=lambda: Path(_env("VAJRA_CORPUS_DIR", str(REPO_ROOT / "data" / "corpus"))))
    index_dir: Path = field(default_factory=lambda: Path(_env("VAJRA_INDEX_DIR", str(REPO_ROOT / "data" / "index"))))
    model_cache_dir: Path = field(default_factory=lambda: Path(_env("VAJRA_MODEL_CACHE", str(REPO_ROOT / "models"))))
    reranker_model: str = field(default_factory=lambda: _env("VAJRA_RERANKER", "Xenova/ms-marco-MiniLM-L-6-v2"))

    # Egress policy: hosts the runtime may open sockets to. Everything else is refused.
    egress_allowlist: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            h.strip() for h in _env("VAJRA_EGRESS_ALLOWLIST", "127.0.0.1,localhost,ollama").split(",") if h.strip()
        )
    )


settings = Settings()
