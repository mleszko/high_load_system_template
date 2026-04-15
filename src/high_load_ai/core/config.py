from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "high-load-system-template"
    app_env: str = Field(
        default="dev",
        validation_alias=AliasChoices("APP_ENV", "app_env"),
    )
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/high_load_ai",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        validation_alias=AliasChoices("CELERY_BROKER_URL", "celery_broker_url"),
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        validation_alias=AliasChoices("CELERY_RESULT_BACKEND", "celery_result_backend"),
    )

    api_keys: str = Field(
        default="local-dev-key",
        validation_alias=AliasChoices("API_KEYS", "API_KEY", "api_keys", "api_key"),
        description="Comma-separated API keys accepted by X-API-Key / Bearer.",
    )

    rate_limit_max_requests: int = Field(
        default=60,
        validation_alias=AliasChoices("RATE_LIMIT_MAX_REQUESTS", "rate_limit_max_requests"),
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices("RATE_LIMIT_WINDOW_SECONDS", "rate_limit_window_seconds"),
    )

    llm_base_url: str = Field(
        default="http://localhost:11434/v1",
        validation_alias=AliasChoices("LLM_BASE_URL", "llm_base_url"),
    )
    llm_api_key: str = Field(
        default="local-placeholder-key",
        validation_alias=AliasChoices("LLM_API_KEY", "llm_api_key"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_MODEL", "llm_model"),
    )
    llm_fallback_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_FALLBACK_MODEL", "llm_fallback_model"),
    )
    llm_timeout_seconds: float = Field(
        default=45.0,
        validation_alias=AliasChoices("LLM_TIMEOUT_SECONDS", "llm_timeout_seconds"),
    )
    llm_fallback_timeout_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices(
            "LLM_FALLBACK_TIMEOUT_SECONDS",
            "llm_fallback_timeout_seconds",
        ),
    )

    circuit_breaker_fail_max: int = Field(
        default=5,
        validation_alias=AliasChoices("CIRCUIT_BREAKER_FAIL_MAX", "circuit_breaker_fail_max"),
    )
    circuit_breaker_reset_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices(
            "CIRCUIT_BREAKER_RESET_SECONDS",
            "circuit_breaker_reset_seconds",
        ),
    )

    exact_cache_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("EXACT_CACHE_ENABLED", "exact_cache_enabled"),
    )
    exact_run_cache_ttl_seconds: int = Field(
        default=30,
        validation_alias=AliasChoices("EXACT_RUN_CACHE_TTL_SECONDS", "exact_run_cache_ttl_seconds"),
    )

    semantic_cache_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("SEMANTIC_CACHE_ENABLED", "semantic_cache_enabled"),
    )
    semantic_cache_embed_mode: Literal["hash", "openai"] = Field(
        default="hash",
        validation_alias=AliasChoices("SEMANTIC_CACHE_EMBED_MODE", "semantic_cache_embed_mode"),
    )
    semantic_cache_embed_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("SEMANTIC_CACHE_EMBED_MODEL", "semantic_cache_embed_model"),
    )
    semantic_cache_min_similarity: float = Field(
        default=0.92,
        validation_alias=AliasChoices("SEMANTIC_CACHE_MIN_SIMILARITY", "semantic_cache_min_similarity"),
    )
    semantic_cache_hash_dimensions: int = Field(
        default=32,
        validation_alias=AliasChoices("SEMANTIC_CACHE_HASH_DIM", "semantic_cache_hash_dimensions"),
    )

    gzip_minimum_size: int = Field(
        default=1000,
        validation_alias=AliasChoices("GZIP_MINIMUM_SIZE", "gzip_minimum_size"),
    )

    llm_stub: bool = Field(
        default=False,
        validation_alias=AliasChoices("LLM_STUB", "llm_stub"),
    )

    tracing_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("TRACING_ENABLED", "tracing_enabled"),
    )

    langfuse_host: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("LANGFUSE_HOST", "langfuse_host"),
    )
    langfuse_public_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY", "langfuse_public_key"),
    )
    langfuse_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY", "langfuse_secret_key"),
    )

    @property
    def llm_stub_enabled(self) -> bool:
        return self.llm_stub or self.app_env == "test"

    @property
    def background_tasks_enabled(self) -> bool:
        return self.app_env != "test"

    @property
    def langfuse_enabled(self) -> bool:
        return self.tracing_enabled and bool(self.langfuse_public_key and self.langfuse_secret_key)


def get_settings() -> Settings:
    return Settings()
