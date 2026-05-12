from app.ingestion.chunking import chunk_document
from app.schemas.documents import Document


def test_chunk_document_preserves_metadata() -> None:
    document = Document(id="doc-1", text="a" * 2500, metadata={"tenant_id": "acme"})

    chunks = chunk_document(document, chunk_size=1000, overlap=100)

    assert len(chunks) == 3
    assert chunks[0].metadata["tenant_id"] == "acme"
    assert chunks[1].metadata["parent_id"] == "doc-1"

