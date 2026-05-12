from app.schemas.common import RetrievedChunk


def reciprocal_rank_fusion(
    result_sets: list[list[RetrievedChunk]],
    k: int = 60,
) -> list[RetrievedChunk]:
    by_id: dict[str, RetrievedChunk] = {}
    scores: dict[str, float] = {}

    for results in result_sets:
        for rank, chunk in enumerate(results, start=1):
            by_id.setdefault(chunk.id, chunk)
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)

    fused = []
    for chunk_id, score in scores.items():
        chunk = by_id[chunk_id].model_copy(update={"score": score})
        fused.append(chunk)
    return sorted(fused, key=lambda item: item.score, reverse=True)

