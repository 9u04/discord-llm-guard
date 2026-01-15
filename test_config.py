"""Test Discord Bot configuration."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings


def test_config():
    """Test if configuration loads correctly."""
    print("=" * 60)
    print("Testing Discord Bot Configuration")
    print("=" * 60)
    
    try:
        settings = get_settings()
        print("\n✅ Configuration loaded successfully!")
        print(f"\nDiscord Settings:")
        print(f"  - Bot Token: {'*' * 20} (hidden)")
        print(f"  - GM Role ID: {settings.discord_gm_role_id}")
        
        print(f"\nLLM Settings:")
        print(f"  - API Key: {'*' * 20} (hidden)")
        print(f"  - Base URL: {settings.llm_base_url}")
        print(f"  - Model: {settings.llm_model}")
        
        print(f"\nDatabase Settings:")
        print(f"  - Database URL: {settings.database_url}")
        
        print(f"\nModeration Settings:")
        print(f"  - History Limit: {settings.history_message_limit}")
        print(f"  - Ban Delete Days: {settings.ban_delete_days}")
        
        print("\n" + "=" * 60)
        print("✅ All configurations are valid!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n❌ Configuration Error:")
        print(f"  {type(e).__name__}: {e}")
        print("\n" + "=" * 60)
        print("Please check your .env file!")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)

