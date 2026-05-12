from qdrant_client import AsyncQdrantClient
from qdrant_client import models
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from app.core.config import Settings
from app.rag.sparse import sparse_text_vector
from app.schemas.common import MetadataFilter, RetrievedChunk

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


class HybridRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key
        )

    async def retrieve(
        self,
        query: str,
        query_vector: list[float],
        filters: MetadataFilter,
    ) -> list[RetrievedChunk]:
        limit = max(
            self.settings.top_k_dense,
            self.settings.top_k_sparse,
            self.settings.top_k_final,
        )
        response = await self.client.query_points(
            collection_name=self.settings.qdrant_collection,
            prefetch=[
                models.Prefetch(
                    query=query_vector,
                    using=DENSE_VECTOR_NAME,
                    limit=self.settings.top_k_dense,
                    filter=qdrant_filter(filters),
                ),
                models.Prefetch(
                    query=sparse_text_vector(query),
                    using=SPARSE_VECTOR_NAME,
                    limit=self.settings.top_k_sparse,
                    filter=qdrant_filter(filters),
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=qdrant_filter(filters),
            limit=limit,
            with_payload=True,
        )
        return [
            RetrievedChunk(
                id=str((point.payload or {}).get("id", point.id)),
                text=str((point.payload or {}).get("text", "")),
                score=float(point.score),
                source=(point.payload or {}).get("source"),
                metadata=dict((point.payload or {}).get("metadata", {})),
            )
            for point in response.points
        ]


def qdrant_filter(filters: MetadataFilter) -> Filter | None:
    conditions: list[FieldCondition] = []
    if filters.tenant_id:
        conditions.append(
            FieldCondition(
                key="metadata.tenant_id", match=MatchValue(value=filters.tenant_id)
            )
        )
    if filters.department:
        conditions.append(
            FieldCondition(
                key="metadata.department", match=MatchValue(value=filters.department)
            )
        )
    if filters.role:
        conditions.append(
            FieldCondition(key="metadata.role", match=MatchValue(value=filters.role))
        )
    if filters.tags:
        conditions.append(
            FieldCondition(key="metadata.tags", match=MatchAny(any=filters.tags))
        )
    return Filter(must=conditions) if conditions else None
