"""Discord bot client."""

from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord.ext import commands, tasks

from src.bot.events import register_event_handlers
from src.database import get_session
from src.database.repository import StatusRepository


class LLMGuardBot(commands.Bot):
    """Discord bot client."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self._status_repo = StatusRepository()

    async def setup_hook(self) -> None:
        """Called before the bot connects."""
        print("Bot initializing...")
        register_event_handlers(self)
        if not self._heartbeat.is_running():
            self._heartbeat.start()

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        print("=" * 50)
        print("Bot is online")
        print(f"User: {self.user.name}")
        print(f"User ID: {self.user.id}")
        print(f"Guilds: {len(self.guilds)}")
        print("=" * 50)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="reports | @me",
            )
        )
        await self._write_status()

    @tasks.loop(seconds=60)
    async def _heartbeat(self) -> None:
        await self._write_status()

    async def _write_status(self) -> None:
        if self.user is None:
            return
        try:
            await asyncio.to_thread(self._write_status_sync)
        except Exception as exc:  # pragma: no cover
            print(f"[DB] heartbeat failed: {type(exc).__name__}: {exc}")

    def _write_status_sync(self) -> None:
        with get_session() as session:
            self._status_repo.upsert_status(
                session,
                active_guilds=len(self.guilds),
                queue_depth=0,
            )


_bot: Optional[LLMGuardBot] = None


def get_bot() -> LLMGuardBot:
    """Get bot singleton."""
    global _bot
    if _bot is None:
        _bot = LLMGuardBot()
    return _bot


