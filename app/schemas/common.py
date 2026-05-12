from typing import Any

from pydantic import BaseModel, Field


class MetadataFilter(BaseModel):
    tenant_id: str | None = None
    department: str | None = None
    role: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

