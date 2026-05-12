from functools import lru_cache

from app.core.config import get_settings
from app.guardrails.policy import GuardrailService
from app.memory.redis_memory import RedisMemoryStore
from app.observability.langfuse_client import LangfuseTracer
from app.rag.embeddings import GeminiEmbeddingService
from app.rag.llm import GeminiLLMGateway
from app.rag.pipeline import RAGPipeline
from app.rag.rerankers import Reranker
from app.rag.retrievers import HybridRetriever


@lru_cache
def get_rag_pipeline() -> RAGPipeline:
    settings = get_settings()
    return RAGPipeline(
        settings=settings,
        embeddings=GeminiEmbeddingService(settings),
        retriever=HybridRetriever(settings=settings),
        reranker=Reranker(),
        llm=GeminiLLMGateway(settings),
        memory=RedisMemoryStore(settings.redis_url),
        guardrails=GuardrailService(),
        tracer=LangfuseTracer(settings),
    )
