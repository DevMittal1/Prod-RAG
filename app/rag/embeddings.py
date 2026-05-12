import asyncio
from typing import Protocol

from google import genai
from google.genai import types

from app.core.config import Settings


class EmbeddingService(Protocol):
    async def embed_query(self, text: str) -> list[float]:
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class GeminiEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self._embed([text], task_type="RETRIEVAL_QUERY")
        return vectors[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._embed(texts, task_type="RETRIEVAL_DOCUMENT")

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        if not self.client:
            return [
                _deterministic_embedding(text, self.settings.gemini_embedding_dimensions)
                for text in texts
            ]

        response = await asyncio.to_thread(
            self.client.models.embed_content,
            model=self.settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self.settings.gemini_embedding_dimensions,
            ),
        )
        return [embedding.values for embedding in response.embeddings]


def _deterministic_embedding(text: str, dimensions: int = 768) -> list[float]:
    vector = [0.0] * dimensions
    for index, byte in enumerate(text.encode("utf-8")):
        vector[index % dimensions] += (byte % 31) / 31.0
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / norm for value in vector]
