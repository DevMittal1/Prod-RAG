import asyncio

from app.schemas.common import RetrievedChunk

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-large") -> None:
        self.model_name = model_name
        self._model = None

    async def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        model = self._load_model()
        if not model:
            return chunks

        pairs = [[query, chunk.text] for chunk in chunks]
        scores = await asyncio.to_thread(model.predict, pairs)
        reranked = [
            chunk.model_copy(update={"score": float(score)})
            for chunk, score in zip(chunks, scores, strict=False)
        ]
        return sorted(reranked, key=lambda item: item.score, reverse=True)

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            return None
        self._model = CrossEncoder(self.model_name)
        return self._model

