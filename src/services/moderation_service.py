"""Moderation service."""

from __future__ import annotations

import asyncio
import discord

from src.config import get_settings
from src.database import get_session
from src.database.models import ReportLog
from src.database.repository import ReportRepository
from src.prompts.templates import build_analysis_prompt
from src.services.discord_service import DiscordService
from src.services.llm_service import LLMDecisionType, LLMService


async def handle_report(
    *,
    report_message: discord.Message,
    reported_message: discord.Message,
    report_reason: str,
) -> None:
    """Handle a user report."""
    settings = get_settings()
    discord_service = DiscordService()
    llm_service = LLMService()
    report_repo = ReportRepository()
    report_id: int | None = None

    if report_message.guild is None:
        await discord_service.send_reply(report_message, "❌ 仅支持服务器内举报。")
        return

    reported_member = await discord_service.get_member(
        report_message.guild, reported_message.author.id
    )
    if reported_member is None:
        await discord_service.send_reply(report_message, "❌ 无法找到被举报用户。")
        return

    user_info = discord_service.get_user_info(reported_member)
    user_history = await discord_service.get_message_history(
        report_message.channel,
        reported_member,
        limit=settings.history_message_limit,
    )

    prompt = build_analysis_prompt(
        reported_message_content=reported_message.content,
        user_history=user_history,
        user_info=user_info,
        report_reason=report_reason,
    )

    try:
        report_id = await asyncio.to_thread(
            _create_report_sync,
            report_repo,
            report_message,
            reported_member,
            reported_message,
            report_reason,
        )
    except Exception as exc:  # pragma: no cover
        print(f"[DB] create_report failed: {type(exc).__name__}: {exc}")

    llm_result = await llm_service.analyze_report(prompt)
    if report_id is not None:
        try:
            await asyncio.to_thread(
                _update_llm_result_sync,
                report_repo,
                report_id,
                llm_result.decision.value,
                llm_result.confidence,
                llm_result.reasoning,
            )
        except Exception as exc:  # pragma: no cover
            print(f"[DB] update_llm_result failed: {type(exc).__name__}: {exc}")

    if llm_result.decision == LLMDecisionType.BAN:
        success = await discord_service.ban_member(
            report_message.guild, reported_member, settings.ban_delete_days
        )
        if success:
            await discord_service.send_reply(
                report_message,
                f"✅ 已封禁用户 {reported_member.mention}。",
            )
        else:
            await discord_service.send_reply(
                report_message,
                "❌ 封禁失败，请检查 Bot 权限。",
            )
        await _update_action_log(
            report_repo, report_id, action="BAN", success=success, error=None
        )
        return

    if llm_result.decision == LLMDecisionType.INVALID_REPORT:
        await discord_service.send_reply(
            report_message,
            "✅ 未发现违规内容，感谢你的反馈。",
        )
        await _update_action_log(
            report_repo, report_id, action="INVALID_REPORT", success=True, error=None
        )
        return

    gm_mention = f"<@&{settings.discord_gm_role_id}>"
    try:
        await discord_service.send_channel_message(
            report_message.channel,
            (
                f"{gm_mention} 收到需要人工审核的举报。\n"
                f"被举报用户：{reported_member.mention}\n"
                f"举报人：{report_message.author.mention}\n"
                f"被举报消息：{reported_message.jump_url}\n"
                f"举报原因：{report_reason}\n"
                f"LLM 理由：{llm_result.reasoning}"
            ),
        )
        await _update_action_log(
            report_repo, report_id, action="NEED_GM", success=True, error=None
        )
    except Exception as exc:  # pragma: no cover
        await _update_action_log(
            report_repo,
            report_id,
            action="NEED_GM",
            success=False,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


async def _update_action_log(
    repo: ReportRepository,
    report_id: int | None,
    action: str,
    success: bool,
    error: str | None,
) -> None:
    if report_id is None:
        return
    try:
        await asyncio.to_thread(
            _update_action_result_sync,
            repo,
            report_id,
            action,
            success,
            error,
        )
    except Exception as exc:  # pragma: no cover
        print(f"[DB] update_action_result failed: {type(exc).__name__}: {exc}")


def _create_report_sync(
    repo: ReportRepository,
    report_message: discord.Message,
    reported_member: discord.Member,
    reported_message: discord.Message,
    report_reason: str,
) -> int:
    with get_session() as session:
        report = ReportLog(
            guild_id=report_message.guild.id if report_message.guild else None,
            channel_id=report_message.channel.id,
            reporter_id=report_message.author.id,
            reporter_name=report_message.author.name,
            reported_user_id=reported_member.id,
            reported_user_name=reported_member.name,
            reported_message_id=reported_message.id,
            reported_message_content=reported_message.content,
            reported_message_url=reported_message.jump_url,
            report_reason=report_reason,
        )
        return repo.create_report(session, report)


def _update_llm_result_sync(
    repo: ReportRepository,
    report_id: int,
    decision: str,
    confidence: float,
    reasoning: str,
) -> None:
    with get_session() as session:
        repo.update_llm_result(
            session,
            report_id=report_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
        )


def _update_action_result_sync(
    repo: ReportRepository,
    report_id: int,
    action: str,
    success: bool,
    error: str | None,
) -> None:
    with get_session() as session:
        repo.update_action_result(
            session,
            report_id=report_id,
            action_taken=action,
            success=success,
            error_message=error,
        )


