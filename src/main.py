"""Entry point."""

import asyncio
import sys
from pathlib import Path

from src.bot.client import get_bot
from src.config import get_settings


async def main() -> None:
    """Run the bot."""
    print("Starting Discord LLM Guard Bot...")

    settings = get_settings()

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    bot = get_bot()
    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        print("\nInterrupted, shutting down...")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())


