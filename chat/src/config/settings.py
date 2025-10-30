"""Application configuration and settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Ocular Triage Chat"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/triage_chat"
    )
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # LLM Providers
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    primary_llm_provider: Literal["anthropic", "openai"] = "anthropic"
    primary_llm_model: str = "claude-3-5-sonnet-20241022"
    fallback_llm_provider: Literal["anthropic", "openai"] = "openai"
    fallback_llm_model: str = "gpt-4o"

    # Neo4j (Knowledge Graph)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"

    # Langfuse (Observability)
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Chainlit
    chainlit_auth_secret: str | None = None
    chainlit_allow_origins: list[str] = ["http://localhost:8000"]

    # External APIs
    paziresh24_api_key: str | None = None
    paziresh24_base_url: str = "https://api.paziresh24.com"

    # Safety & Compliance
    max_session_duration_minutes: int = 30
    require_consent: bool = True
    enable_red_flag_detection: bool = True
    log_all_interactions: bool = True

    # Performance
    max_tokens_per_request: int = 4096
    request_timeout_seconds: int = 30
    max_retries: int = 3


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application configuration
    """
    return Settings()
