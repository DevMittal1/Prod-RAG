from app.rag.sparse import sparse_text_vector


def test_sparse_text_vector_is_deterministic_and_sorted() -> None:
    first = sparse_text_vector("Policy policy ID-123")
    second = sparse_text_vector("Policy policy ID-123")

    assert first.indices == second.indices
    assert first.values == second.values
    assert first.indices == sorted(first.indices)
    assert len(first.indices) == len(first.values)


def test_sparse_text_vector_handles_empty_text() -> None:
    vector = sparse_text_vector("   ")

    assert vector.indices == []
    assert vector.values == []
