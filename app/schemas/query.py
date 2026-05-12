from pydantic import BaseModel, Field

from app.schemas.common import MetadataFilter, RetrievedChunk


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    user_id: str
    session_id: str
    filters: MetadataFilter = Field(default_factory=MetadataFilter)
    top_k: int | None = Field(default=None, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    chunks: list[RetrievedChunk]
    trace_id: str | None = None

