from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    text: str = Field(min_length=1)
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIngestRequest(BaseModel):
    tenant_id: str
    documents: list[Document]


class JobResponse(BaseModel):
    job_id: str
    status: str

