"""Prompt templates."""

from __future__ import annotations

from typing import Iterable


def _format_history(history: Iterable[dict]) -> str:
    lines = []
    for item in history:
        content = item.get("content", "").strip() or "(空消息)"
        created_at = item.get("created_at", "unknown")
        lines.append(f"- {created_at}: {content}")
    return "\n".join(lines) if lines else "(无历史消息)"


def build_analysis_prompt(
    *,
    reported_message_content: str,
    user_history: list[dict],
    user_info: dict,
    report_reason: str,
) -> str:
    """Build prompt for LLM analysis."""
    history_text = _format_history(user_history)
    roles = ", ".join(user_info.get("roles", [])) or "(无角色)"

    return (
        "你是 Discord 频道的内容审核助手，请根据以下信息判断是否需要封禁。\n"
        "输出三种结论之一：BAN / INVALID_REPORT / NEED_GM。\n\n"
        f"[被举报消息]\n{reported_message_content}\n\n"
        f"[举报原因]\n{report_reason}\n\n"
        "[被举报用户信息]\n"
        f"- ID: {user_info.get('id')}\n"
        f"- 名称: {user_info.get('name')}\n"
        f"- 创建时间: {user_info.get('created_at')}\n"
        f"- 加入时间: {user_info.get('joined_at')}\n"
        f"- 是否机器人: {user_info.get('is_bot')}\n"
        f"- 角色: {roles}\n\n"
        "[最近历史消息]\n"
        f"{history_text}\n\n"
        "请给出结论、置信度(0-1)与理由。\n"
        "仅输出 JSON，不要包含其他文字。"
    )


