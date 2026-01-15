"""Helpers."""

from __future__ import annotations

import re


def strip_bot_mention(content: str, bot_user_id: int) -> str:
    """Remove bot mention from message content."""
    mention_pattern = rf"<@!?{bot_user_id}>"
    cleaned = re.sub(mention_pattern, "", content).strip()
    return cleaned


def normalize_report_reason(content: str, bot_user_id: int) -> str:
    """Get report reason text with a fallback."""
    reason = strip_bot_mention(content, bot_user_id).strip()
    return reason or "未提供举报原因"


