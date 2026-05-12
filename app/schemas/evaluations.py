from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str] = Field(default_factory=list)
    reference_answer: str | None = None


class EvaluationResponse(BaseModel):
    faithfulness: float
    context_precision: float
    answer_relevance: float
    notes: list[str]

