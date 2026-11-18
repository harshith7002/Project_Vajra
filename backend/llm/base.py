"""Provider-neutral LLM interface.

Every backend (Ollama now, optional Gemini later) returns the same `LLMResult`,
including token counts and timing straight from the provider. Phase 3's tracing
reads these fields, so no number in a trace is estimated by our own code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ChatMessage:
    role: Role
    content: str


@dataclass
class LLMResult:
    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int  # includes hidden reasoning tokens when the model "thinks"
    latency_s: float  # wall clock for the whole call
    thinking: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens_per_s(self) -> float:
        return self.output_tokens / self.latency_s if self.latency_s > 0 else 0.0


class LLMClient(Protocol):
    provider: str
    model: str

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResult: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...
