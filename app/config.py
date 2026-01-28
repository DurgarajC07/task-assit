"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    app_name: str = "Task Assistant"
    debug: bool = False
    port: int = 8000
    allowed_origins: str = "*"

    # Database
    database_url: str = "sqlite+aiosqlite:///./task_assistant.db"

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # LLM Configuration
    llm_provider: str = "grok"  # Options: claude, openai, gemini, grok
    llm_model: str = "llama-3.1-8b-instant"  # Default model for Grok (free tier)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""

    # WebSocket
    ws_heartbeat_interval: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_15min: int = 5

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def get_allowed_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string."""
        if self.allowed_origins == "*":
            return ["*"]
        if isinstance(self.allowed_origins, str):
            origins = [origin.strip() for origin in self.allowed_origins.split(",")]
            return [o for o in origins if o]  # Filter empty strings
        return self.allowed_origins


settings = Settings()
