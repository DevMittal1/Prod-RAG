from fastapi import APIRouter

from app.evaluation.rag import evaluate_rag_sample
from app.schemas.evaluations import EvaluationRequest, EvaluationResponse

router = APIRouter()


@router.post("/evaluations/rag", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    return evaluate_rag_sample(request)

