from datetime import datetime
from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_rag_pipeline, get_current_user
from app.db.mongodb import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.rag.pipeline import RAGPipeline

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
) -> QueryResponse:
    response = await pipeline.answer(request)
    
    # Save usage to MongoDB
    await db.usage_logs.insert_one({
        "user_id": current_user["id"],
        "query_text": request.query,
        "answer_text": response.answer,
        # Assume response might have tokens in the future
        "tokens_used": getattr(response, "tokens_used", None),
        "created_at": datetime.utcnow()
    })
    
    return response

