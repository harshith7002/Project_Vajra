"""LLM-as-judge scorers (local model, structured JSON output).

faithfulness: split the answer into atomic claims, mark each as supported or not
              by the retrieved context. Score = supported / total claims.
              It measures grounding, NOT truth: a correct fact that is not in the
              context counts as unsupported.
correctness:  compare the answer with the gold answer -> correct / partial / incorrect.

Limitation (stated in the README): the judge is the same 2B model that writes the
answers. The negative control in answer_eval.py measures how well it catches
unsupported claims, so the faithfulness number comes with its own error bar.
"""
from __future__ import annotations

import json

from backend.llm.base import ChatMessage, LLMClient, LLMResult

FAITHFULNESS_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"claim": {"type": "string"}, "supported": {"type": "boolean"}},
                "required": ["claim", "supported"],
            },
        }
    },
    "required": ["claims"],
}

CORRECTNESS_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["correct", "partial", "incorrect"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
}

FAITH_SYSTEM = (
    "You check whether an ANSWER is grounded in a CONTEXT. Break the ANSWER into short atomic factual claims "
    "(ignore citation markers like [1]). For each claim set supported=true ONLY if the CONTEXT states it or it "
    "follows directly from the CONTEXT; otherwise supported=false. Use your own knowledge for nothing. "
    "Return JSON."
)

CORRECT_SYSTEM = (
    "You grade an ANSWER against a GOLD answer to the same QUESTION. verdict=correct if it contains the key facts "
    "of the GOLD answer and nothing contradicting it; partial if it has some key facts but misses or garbles others; "
    "incorrect if it is wrong, contradicts GOLD, or says the information was not found. Return JSON."
)


def _parse(result: LLMResult) -> dict | None:
    try:
        return json.loads(result.text)
    except (json.JSONDecodeError, TypeError):
        return None


def judge_faithfulness(llm: LLMClient, context: str, answer: str) -> tuple[dict | None, LLMResult]:
    r = llm.chat(
        [ChatMessage("system", FAITH_SYSTEM), ChatMessage("user", f"CONTEXT:\n{context}\n\nANSWER:\n{answer}")],
        json_schema=FAITHFULNESS_SCHEMA,
    )
    return _parse(r), r


def judge_correctness(llm: LLMClient, question: str, gold: str, answer: str) -> tuple[dict | None, LLMResult]:
    r = llm.chat(
        [ChatMessage("system", CORRECT_SYSTEM),
         ChatMessage("user", f"QUESTION: {question}\nGOLD: {gold}\nANSWER: {answer}")],
        json_schema=CORRECTNESS_SCHEMA,
    )
    return _parse(r), r
