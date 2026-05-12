from uuid import NAMESPACE_URL, uuid5

from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import Settings
from app.rag.embeddings import _deterministic_embedding
from app.rag.retrievers import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME
from app.rag.sparse import sparse_text_vector
from app.schemas.documents import Document


class DocumentIndexer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.qdrant = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key
        )
        self.gemini = (
            genai.Client(api_key=settings.gemini_api_key)
            if settings.gemini_api_key
            else None
        )

    def ensure_indexes(self) -> None:
        collections = {
            collection.name for collection in self.qdrant.get_collections().collections
        }
        if self.settings.qdrant_collection not in collections:
            self.qdrant.create_collection(
                collection_name=self.settings.qdrant_collection,
                vectors_config={
                    DENSE_VECTOR_NAME: VectorParams(
                        size=self.settings.gemini_embedding_dimensions,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    SPARSE_VECTOR_NAME: models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=False)
                    )
                },
            )
            self._create_payload_indexes()

    def index(self, documents: list[Document]) -> int:
        self.ensure_indexes()
        points = []
        vectors = self._embed_documents([document.text for document in documents])
        for document, vector in zip(documents, vectors, strict=False):
            payload = {
                "id": document.id,
                "text": document.text,
                "source": document.source,
                "metadata": document.metadata,
            }
            points.append(
                PointStruct(
                    id=str(_qdrant_point_id(document.id)),
                    vector={
                        DENSE_VECTOR_NAME: vector,
                        SPARSE_VECTOR_NAME: sparse_text_vector(document.text),
                    },
                    payload=payload,
                )
            )
        if points:
            self.qdrant.upsert(
                collection_name=self.settings.qdrant_collection, points=points
            )
        return len(points)

    def _embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.gemini:
            return [
                _deterministic_embedding(
                    text, self.settings.gemini_embedding_dimensions
                )
                for text in texts
            ]
        response = self.gemini.models.embed_content(
            model=self.settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.settings.gemini_embedding_dimensions,
            ),
        )
        return [embedding.values for embedding in response.embeddings]

    def _create_payload_indexes(self) -> None:
        for field_name in (
            "metadata.tenant_id",
            "metadata.department",
            "metadata.role",
            "metadata.tags",
        ):
            self.qdrant.create_payload_index(
                collection_name=self.settings.qdrant_collection,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )


def _qdrant_point_id(document_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, document_id))
