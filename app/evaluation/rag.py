from app.schemas.evaluations import EvaluationRequest, EvaluationResponse


def evaluate_rag_sample(request: EvaluationRequest) -> EvaluationResponse:
    answer_tokens = set(request.answer.lower().split())
    context_text = " ".join(request.contexts).lower()
    reference_tokens = set((request.reference_answer or request.question).lower().split())

    faithfulness = _overlap_ratio(answer_tokens, set(context_text.split())) if context_text else 0.0
    context_precision = sum(1 for context in request.contexts if _has_overlap(request.question, context)) / max(
        len(request.contexts), 1
    )
    answer_relevance = _overlap_ratio(answer_tokens, reference_tokens)

    notes = []
    if faithfulness < 0.2:
        notes.append("Low lexical support from supplied contexts; run a model-graded faithfulness check.")
    if context_precision < 0.5:
        notes.append("Retrieved contexts may be weak for the question.")

    return EvaluationResponse(
        faithfulness=round(faithfulness, 3),
        context_precision=round(context_precision, 3),
        answer_relevance=round(answer_relevance, 3),
        notes=notes,
    )


def _overlap_ratio(left: set[str], right: set[str]) -> float:
    if not left:
        return 0.0
    return len(left & right) / len(left)


def _has_overlap(left: str, right: str) -> bool:
    return bool(set(left.lower().split()) & set(right.lower().split()))

