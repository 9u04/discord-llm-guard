"""Quick Discord Bot connection test - validates token format and configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings


def test_configuration():
    """Test if configuration is loaded correctly."""
    print("\n" + "=" * 60)
    print("🔍 Discord Bot Configuration Test")
    print("=" * 60)
    
    try:
        settings = get_settings()
        
        print("\n✅ Configuration File Status:")
        print("   - .env file found and loaded")
        
        # Check Discord token
        token = settings.discord_token
        print(f"\n✅ Discord Token:")
        print(f"   - Length: {len(token)} characters")
        print(f"   - Preview: {token[:20]}...{token[-10:]}")
        
        if not token or len(token) < 50:
            print("   ❌ Token seems invalid (too short)")
            return False
        else:
            print("   ✅ Token format looks valid")
        
        # Check GM Role ID
        gm_role_id = settings.discord_gm_role_id
        print(f"\n✅ GM Role ID:")
        print(f"   - Value: {gm_role_id}")
        print(f"   - Type: {type(gm_role_id).__name__}")
        
        if not isinstance(gm_role_id, int) or gm_role_id <= 0:
            print("   ❌ Role ID seems invalid")
            return False
        else:
            print("   ✅ Role ID format looks valid")
        
        # Check LLM settings
        print(f"\n✅ LLM Configuration:")
        print(f"   - API Key: {'*' * 20}...")
        print(f"   - Base URL: {settings.llm_base_url}")
        print(f"   - Model: {settings.llm_model}")
        
        if not settings.llm_api_key:
            print("   ⚠️  LLM API Key not configured (optional for connection test)")
        
        print("\n" + "=" * 60)
        print("✅ All configurations look valid!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   1. Your Discord Bot token is configured")
        print("   2. Your GM role ID is configured")
        print("   3. You can now run the bot with: python -m src.main")
        print("   4. Or run connection test: python test_bot_connection.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration Error:")
        print(f"   {type(e).__name__}: {e}")
        print("\n📋 Troubleshooting:")
        print("   1. Make sure .env file exists in project root")
        print("   2. Check that DISCORD_TOKEN is set")
        print("   3. Check that DISCORD_GM_ROLE_ID is set")
        print("   4. Make sure .env format is correct (KEY=VALUE)")
        return False


if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)

