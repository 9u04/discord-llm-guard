"""Bot event handlers."""

from __future__ import annotations

import discord
from discord.ext import commands

from src.services.moderation_service import handle_report
from src.utils.helpers import normalize_report_reason


def register_event_handlers(bot: commands.Bot) -> None:
    """Register bot event handlers."""

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Handle all messages and detect reports."""
        if message.author == bot.user:
            return

        if message.guild is None:
            return

        if bot.user is None or bot.user not in message.mentions:
            await bot.process_commands(message)
            return

        if message.reference is None or message.reference.message_id is None:
            await message.reply(
                "❌ 请通过**引用消息**来举报\n"
                "操作方式：右键目标消息 → 回复 → 输入 `@Bot 这是垃圾`"
            )
            return

        referenced = message.reference.resolved
        if isinstance(referenced, discord.Message):
            reported_message = referenced
        else:
            try:
                reported_message = await message.channel.fetch_message(
                    message.reference.message_id
                )
            except discord.NotFound:
                await message.reply("❌ 无法找到被引用的消息")
                return
            except discord.Forbidden:
                await message.reply("❌ 没有权限访问该消息")
                return
            except discord.HTTPException:
                await message.reply("❌ 获取被引用消息失败")
                return

        if bot.user is not None and reported_message.author == bot.user:
            await message.reply("❌ 不能举报 Bot 的消息")
            return

        if reported_message.author == message.author:
            await message.reply("❌ 不能举报自己的消息")
            return

        report_reason = normalize_report_reason(message.content, bot.user.id)

        await message.reply("✅ 已收到你的举报，正在处理中...")
        await handle_report(
            report_message=message,
            reported_message=reported_message,
            report_reason=report_reason,
        )

        await bot.process_commands(message)


