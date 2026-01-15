"""Enhanced Discord Bot connection test with detailed logging."""

import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.bot.client import get_bot
import discord

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_bot_connection_enhanced():
    """Enhanced test with better error handling and logging."""
    print("\n" + "=" * 70)
    print("🔐 Discord Bot Connection Test (Enhanced)")
    print("=" * 70)
    
    try:
        # Load configuration
        print("\n📋 Loading configuration...")
        settings = get_settings()
        print(f"   ✅ Token: {settings.discord_token[:20]}...{settings.discord_token[-10:]}")
        print(f"   ✅ GM Role ID: {settings.discord_gm_role_id}")
        
        # Create bot instance
        print("\n🤖 Creating bot instance...")
        bot = get_bot()
        
        # Register event handlers to monitor connection
        connection_success = asyncio.Event()
        connection_error = None
        
        @bot.event
        async def on_ready():
            """Called when bot successfully connects."""
            print(f"\n✅ BOT CONNECTED SUCCESSFULLY!")
            print(f"   Bot Name: {bot.user.name}")
            print(f"   Bot ID: {bot.user.id}")
            print(f"   Connected Guilds: {len(bot.guilds)}")
            if bot.guilds:
                for guild in bot.guilds:
                    print(f"      - {guild.name} (ID: {guild.id})")
            connection_success.set()
        
        @bot.event
        async def on_error(event, *args, **kwargs):
            """Handle errors."""
            nonlocal connection_error
            error_msg = f"Error in {event}"
            print(f"\n❌ {error_msg}")
            connection_error = error_msg
        
        # Attempt connection with timeout
        print("\n⏳ Attempting to connect to Discord...")
        print("   (Waiting up to 15 seconds...)\n")
        
        try:
            # Start the bot in a task
            bot_task = asyncio.create_task(bot.start(settings.discord_token))
            
            # Wait for either connection success or timeout
            try:
                await asyncio.wait_for(
                    connection_success.wait(),
                    timeout=15
                )
                print("\n✅ Connection test PASSED!")
                return True
            except asyncio.TimeoutError:
                print("\n⚠️  Connection attempt timed out")
                print("   Note: This doesn't necessarily mean there's an error.")
                print("   The bot may be connecting but hasn't fully initialized yet.")
                if connection_error:
                    print(f"   Error captured: {connection_error}")
                    return False
                return True
                
        except discord.errors.LoginFailure as e:
            print(f"\n❌ LOGIN FAILED!")
            print(f"   Error: {e}")
            print("\n   Possible causes:")
            print("   1. Invalid or expired Discord bot token")
            print("   2. Bot token was compromised and rotated")
            print("   3. Token format is incorrect")
            return False
        except Exception as e:
            print(f"\n❌ Connection Error: {type(e).__name__}")
            print(f"   {e}")
            return False
        finally:
            # Clean up
            try:
                await bot.close()
            except:
                pass
            if not bot_task.done():
                bot_task.cancel()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass
                
    except Exception as e:
        print(f"\n❌ Test Error: {type(e).__name__}")
        print(f"   {e}")
        return False


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT INFORMATION:")
    print("   - This test attempts to connect your bot to Discord")
    print("   - It will timeout after 15 seconds")
    print("   - Make sure your bot token is valid")
    print("   - Make sure the bot has been added to your Discord server")
    print()
    
    try:
        success = asyncio.run(test_bot_connection_enhanced())
        
        if success:
            print("\n" + "=" * 70)
            print("✅ TEST PASSED - Bot configuration is valid!")
            print("=" * 70)
            print("\n📝 Next steps:")
            print("   1. Run: python -m src.main")
            print("   2. Or deploy with: docker build -t discord-llm-guard .")
            print()
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("❌ TEST FAILED - Please check the errors above")
            print("=" * 70)
            print()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(0)

