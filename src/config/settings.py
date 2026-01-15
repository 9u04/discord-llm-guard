"""Application settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    # Discord
    discord_token: str = Field(..., description="Discord Bot token")
    discord_gm_role_id: int = Field(..., description="GM role ID")

    # LLM
    llm_api_key: str = Field(..., description="LLM API key")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="LLM API base URL",
    )
    llm_model: str = Field(default="gpt-4o", description="LLM model name")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/bot.db", description="Database URL"
    )

    # Moderation
    history_message_limit: int = Field(default=10, description="History limit")
    ban_delete_days: int = Field(default=7, description="Ban delete days")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


