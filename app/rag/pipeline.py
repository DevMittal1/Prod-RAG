from uuid import uuid4

import structlog

from app.core.config import Settings
from app.guardrails.policy import GuardrailService
from app.memory.base import MemoryStore
from app.observability.base import TraceClient
from app.rag.embeddings import EmbeddingService
from app.rag.llm import LLMGateway
from app.rag.rerankers import Reranker
from app.rag.retrievers import HybridRetriever
from app.schemas.common import RetrievedChunk
from app.schemas.query import QueryRequest, QueryResponse

logger = structlog.get_logger(__name__)


class RAGPipeline:
    def __init__(
        self,
        settings: Settings,
        embeddings: EmbeddingService,
        retriever: HybridRetriever,
        reranker: Reranker,
        llm: LLMGateway,
        memory: MemoryStore,
        guardrails: GuardrailService,
        tracer: TraceClient,
    ) -> None:
        self.settings = settings
        self.embeddings = embeddings
        self.retriever = retriever
        self.reranker = reranker
        self.llm = llm
        self.memory = memory
        self.guardrails = guardrails
        self.tracer = tracer

    async def answer(self, request: QueryRequest) -> QueryResponse:
        trace_id = uuid4().hex
        
        with self.tracer.safe_start_trace(trace_id, "rag_pipeline", {"query": request.query}) as trace:
            self.guardrails.validate_input(request.query)

            conversation = await self.memory.get_session(request.user_id, request.session_id)
            query_vector = await self.embeddings.embed_query(request.query)
            retrieved = await self.retriever.retrieve(
                query=request.query,
                query_vector=query_vector,
                filters=request.filters,
            )
            reranked = await self.reranker.rerank(request.query, retrieved)
            top_k = request.top_k or self.settings.top_k_final
            chunks = reranked[:top_k]

            answer = await self.llm.generate(
                query=request.query,
                chunks=chunks,
                conversation=conversation,
            )
            self.guardrails.validate_output(answer)
            await self.memory.append_turn(request.user_id, request.session_id, request.query, answer)
            
            if trace and hasattr(trace, 'update'):
                trace.update(output={"answer": answer, "chunk_count": len(chunks)})

            return QueryResponse(answer=answer, chunks=chunks, trace_id=trace_id)


def format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{idx + 1}] {chunk.text}" for idx, chunk in enumerate(chunks))
