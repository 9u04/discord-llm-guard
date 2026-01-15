"""Discord service."""

from __future__ import annotations

from typing import Any

import discord


class DiscordService:
    """Discord API wrapper."""

    async def get_member(
        self, guild: discord.Guild, user_id: int
    ) -> discord.Member | None:
        """Get a guild member by ID."""
        member = guild.get_member(user_id)
        if member:
            return member
        try:
            return await guild.fetch_member(user_id)
        except discord.NotFound:
            return None
        except discord.Forbidden:
            return None
        except discord.HTTPException:
            return None

    def get_user_info(self, member: discord.Member) -> dict[str, Any]:
        """Get user info for prompt building."""
        return {
            "id": member.id,
            "name": member.name,
            "created_at": member.created_at.isoformat(),
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "is_bot": member.bot,
            "roles": [role.name for role in member.roles],
        }

    async def get_message_history(
        self,
        channel: discord.abc.Messageable,
        user: discord.abc.User,
        limit: int,
        scan_limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent message history for a user."""
        if not hasattr(channel, "history"):
            return []

        history_items: list[dict[str, Any]] = []
        max_scan = scan_limit or max(limit * 5, 50)

        async for msg in channel.history(limit=max_scan):  # type: ignore[attr-defined]
            if msg.author.id != user.id:
                continue
            history_items.append(
                {
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "url": msg.jump_url,
                }
            )
            if len(history_items) >= limit:
                break

        return history_items

    async def send_reply(
        self, message: discord.Message, content: str, mention_author: bool = True
    ) -> None:
        """Reply to a message."""
        await message.reply(content, mention_author=mention_author)

    async def send_channel_message(
        self, channel: discord.abc.Messageable, content: str
    ) -> None:
        """Send a message to a channel."""
        await channel.send(content)

    async def ban_member(
        self, guild: discord.Guild, member: discord.Member, delete_message_days: int
    ) -> bool:
        """Ban a member."""
        try:
            await guild.ban(member, delete_message_days=delete_message_days)
            return True
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False


