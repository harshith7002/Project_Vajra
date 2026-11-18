"""Ollama backend for the LLMClient interface (local-only, egress-guarded)."""
from __future__ import annotations

import time
from typing import Any

import httpx

from backend.config import settings
from backend.llm.base import ChatMessage, LLMResult
from backend.security.egress_guard import check_url


class OllamaClient:
    provider = "ollama"

    def __init__(
        self,
        model: str | None = None,
        embed_model: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.model = model or settings.chat_model
        self.embed_model = embed_model or settings.embed_model
        self.base_url = (base_url or settings.ollama_url).rstrip("/")
        self.timeout_s = timeout_s or settings.llm_timeout_s
        check_url(self.base_url, "OLLAMA_CLIENT_INIT")
        self._http = httpx.Client(base_url=self.base_url, timeout=self.timeout_s)

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResult:
        check_url(self.base_url, "LOCAL_LLM_INFERENCE")
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": {
                "temperature": temperature,
                "seed": 7,  # fixed seed so eval runs are repeatable on the same machine
                "num_predict": max_tokens or settings.llm_max_tokens,
                "num_ctx": 8192,
            },
        }
        if json_schema is not None:
            payload["format"] = json_schema  # Ollama structured outputs (constrained decoding)
        start = time.perf_counter()
        resp = self._http.post("/api/chat", json=payload)
        latency = time.perf_counter() - start
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message", {})
        return LLMResult(
            text=(msg.get("content") or "").strip(),
            thinking=msg.get("thinking") or "",
            model=self.model,
            provider=self.provider,
            input_tokens=int(data.get("prompt_eval_count") or 0),
            output_tokens=int(data.get("eval_count") or 0),
            latency_s=latency,
            raw={k: data.get(k) for k in ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration", "done_reason")},
        )

    def embed(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        check_url(self.base_url, "LOCAL_EMBEDDING")
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            resp = self._http.post("/api/embed", json={"model": self.embed_model, "input": texts[i : i + batch_size]})
            resp.raise_for_status()
            out.extend(resp.json()["embeddings"])
        return out
