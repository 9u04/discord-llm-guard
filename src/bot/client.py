"""Discord bot client."""

from typing import Optional

import discord
from discord.ext import commands


class LLMGuardBot(commands.Bot):
    """Discord bot client."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self) -> None:
        """Called before the bot connects."""
        print("Bot initializing...")

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


_bot: Optional[LLMGuardBot] = None


def get_bot() -> LLMGuardBot:
    """Get bot singleton."""
    global _bot
    if _bot is None:
        _bot = LLMGuardBot()
    return _bot

