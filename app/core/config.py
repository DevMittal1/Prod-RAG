from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Production RAG"
    environment: str = "local"
    log_level: str = "INFO"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = Field(default=768, ge=1)

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = "api_key"
    qdrant_collection: str = "documents"

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    top_k_dense: int = Field(default=30, ge=1)
    top_k_sparse: int = Field(default=30, ge=1)
    top_k_final: int = Field(default=8, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
