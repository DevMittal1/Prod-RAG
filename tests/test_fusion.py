from app.rag.fusion import reciprocal_rank_fusion
from app.schemas.common import RetrievedChunk


def test_reciprocal_rank_fusion_merges_and_sorts_by_score() -> None:
    first = [
        RetrievedChunk(id="a", text="A", score=0.9),
        RetrievedChunk(id="b", text="B", score=0.8),
    ]
    second = [
        RetrievedChunk(id="b", text="B", score=0.95),
        RetrievedChunk(id="c", text="C", score=0.7),
    ]

    result = reciprocal_rank_fusion([first, second], k=60)

    assert [chunk.id for chunk in result] == ["b", "a", "c"]
    assert result[0].score > result[1].score

