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

class DocumentMetadataResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    filename: str
    s3_key: str
    content_type: str
    size: int
    created_at: str

class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadataResponse]

