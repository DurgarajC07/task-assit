"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    app_name: str = "Task Assistant SaaS"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    port: int = 8000
    allowed_origins: str = "*"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/task_assistant"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300  # 5 minutes
    redis_session_ttl: int = 3600  # 1 hour

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    encryption_key: str = secrets.token_urlsafe(32)  # For encrypting provider credentials
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_min_length: int = 8
    
    # API Keys
    api_key_prefix: str = "ta_"  # Task Assistant API key prefix
    api_key_length: int = 32

    # Rate Limiting (per tenant)
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    auth_rate_limit_per_15min: int = 10
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections_per_user: int = 5

    # LLM Configuration (Legacy - will be moved to database)
    llm_provider: str = "openai"  # Default for backward compatibility
    llm_model: str = "gpt-4"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""

    # Celery / Background Tasks
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_time_limit: int = 300  # 5 minutes
    celery_task_soft_time_limit: int = 240  # 4 minutes

    # Vector Store
    vector_store_type: str = "pinecone"  # pinecone, qdrant, weaviate
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "task-assistant"
    
    # Object Storage
    storage_type: str = "local"  # local, s3, azure
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_s3_region: str = "us-east-1"
    
    # Monitoring & Observability
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # CORS
    cors_allow_credentials: bool = True
    cors_max_age: int = 3600
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def get_allowed_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string."""
        if self.allowed_origins == "*":
            return ["*"]
        if isinstance(self.allowed_origins, str):
            origins = [origin.strip() for origin in self.allowed_origins.split(",")]
            return [o for o in origins if o]  # Filter empty strings
        return self.allowed_origins
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
