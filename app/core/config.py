from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Production RAG"
    app_version: str = "1.0.0"
    environment: str = "local"
    log_level: str = "INFO"
    platform_profile: str = "enterprise"
    document_domain: str = "legal"

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
    document_chunk_size: int = Field(default=1200, ge=100)
    document_chunk_overlap: int = Field(default=150, ge=0)
    legal_citations_required: bool = True
    legal_required_metadata_fields: str = "tenant_id,department,role,tags"

    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "production_rag"

    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "production-rag-docs"
    s3_region: str = "us-east-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
