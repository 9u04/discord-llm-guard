"""LLM service."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

from src.config import get_settings


class LLMDecisionType(str, Enum):
    """Decision types returned by LLM."""

    BAN = "BAN"
    INVALID_REPORT = "INVALID_REPORT"
    NEED_GM = "NEED_GM"


@dataclass(frozen=True)
class LLMDecision:
    """LLM analysis result."""

    decision: LLMDecisionType
    confidence: float
    reasoning: str


class LLMService:
    """LLM service using OpenAI-compatible API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    async def analyze_report(self, prompt: str) -> LLMDecision:
        """Analyze report and return a decision."""
        system_prompt = (
            "你是 Discord 频道的内容审核助手。"
            "请只输出 JSON，不要包含多余文字。"
            "JSON 格式："
            '{"decision":"BAN|INVALID_REPORT|NEED_GM","confidence":0-1,'
            '"reasoning":"简短理由"}'
            "字段名必须使用 decision/confidence/reasoning。"
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except Exception:
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
            except Exception as exc:  # pragma: no cover - network/runtime errors
                return LLMDecision(
                    decision=LLMDecisionType.NEED_GM,
                    confidence=0.0,
                    reasoning=f"LLM 调用失败：{type(exc).__name__}",
                )

        content = response.choices[0].message.content or ""
        if os.getenv("LLM_DEBUG_RAW"):
            print(f"[LLM_RAW] {content}")
        return _parse_llm_response(content)


def _parse_llm_response(content: str) -> LLMDecision:
    """Parse LLM response into structured decision."""
    data = _extract_json(content)
    if not isinstance(data, dict):
        guessed = _guess_decision_from_text(content)
        if guessed is not None:
            return LLMDecision(
                decision=guessed,
                confidence=0.0,
                reasoning="LLM 返回非 JSON，已使用兜底解析。",
            )
        if os.getenv("LLM_DEBUG_RAW"):
            print(f"[LLM_RAW] {content}")
        return LLMDecision(
            decision=LLMDecisionType.NEED_GM,
            confidence=0.0,
            reasoning="LLM 返回无法解析。",
        )

    decision_raw = str(
        data.get("decision", data.get("conclusion", data.get("result", "")))
    ).upper()
    decision = (
        LLMDecisionType(decision_raw)
        if decision_raw in LLMDecisionType._value2member_map_
        else LLMDecisionType.NEED_GM
    )
    confidence = _normalize_confidence(data.get("confidence"))
    reasoning = str(data.get("reasoning", data.get("reason", ""))).strip() or "未提供理由"

    return LLMDecision(
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
    )


def _extract_json(content: str) -> dict | None:
    """Extract JSON object from content."""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    candidate = _extract_first_json_object(content)
    if not candidate:
        return None

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_first_json_object(content: str) -> str | None:
    """Extract first balanced JSON object from text."""
    start = content.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(content)):
        ch = content[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return content[start : idx + 1]
    return None


def _normalize_confidence(value: object) -> float:
    """Normalize confidence to 0~1."""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _guess_decision_from_text(content: str) -> LLMDecisionType | None:
    """Guess decision type from free-form content."""
    text = content.upper()
    for decision in LLMDecisionType:
        if decision.value in text:
            return decision
    return None


