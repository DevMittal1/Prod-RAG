from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_rag_pipeline
from app.schemas.query import QueryRequest, QueryResponse
from app.rag.pipeline import RAGPipeline

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, pipeline: RAGPipeline = Depends(get_rag_pipeline)) -> QueryResponse:
    return await pipeline.answer(request)

