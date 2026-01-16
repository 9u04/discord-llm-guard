"""Test Discord Bot connection."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.bot.client import get_bot


async def test_bot_connection():
    """Test if the bot can connect to Discord."""
    print("=" * 60)
    print("Testing Discord Bot Connection")
    print("=" * 60)
    
    try:
        settings = get_settings()
        print(f"\n✅ Configuration loaded")
        print(f"   Token: {'*' * 20}")
        print(f"   GM Role ID: {settings.discord_gm_role_id}")
        
        bot = get_bot()
        print(f"\n⏳ Connecting to Discord...")
        print("   (This will take a few seconds...)")
        print("   Press Ctrl+C to stop")
        
        # Set a timeout of 10 seconds to test connection
        async def run_with_timeout():
            try:
                await asyncio.wait_for(bot.start(settings.discord_token), timeout=10)
            except asyncio.TimeoutError:
                # Timeout is expected, we just want to verify connection
                pass
        
        await run_with_timeout()
        
    except asyncio.TimeoutError:
        print("\n✅ Bot connection test completed!")
        print("   (Connection timeout after 10s is expected for this test)")
        
    except Exception as e:
        print(f"\n❌ Connection Error:")
        print(f"   {type(e).__name__}: {e}")
        return False
    finally:
        # Ensure the bot is closed
        if bot._ready.is_set():
            await bot.close()
    
    return True


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT:")
    print("   Make sure you have filled in real values in .env:")
    print("   - DISCORD_TOKEN: Your actual Bot Token")
    print("   - DISCORD_GM_ROLE_ID: Your actual GM role ID")
    print()
    
    try:
        success = asyncio.run(test_bot_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✅ Test interrupted (expected)")
        sys.exit(0)



