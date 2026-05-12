from app.schemas.documents import Document


def chunk_document(document: Document, chunk_size: int = 1200, overlap: int = 150) -> list[Document]:
    if len(document.text) <= chunk_size:
        return [document]

    chunks: list[Document] = []
    start = 0
    index = 0
    while start < len(document.text):
        end = min(start + chunk_size, len(document.text))
        text = document.text[start:end]
        chunks.append(
            Document(
                id=f"{document.id}:{index}",
                text=text,
                source=document.source,
                metadata={**document.metadata, "parent_id": document.id, "chunk_index": index},
            )
        )
        if end == len(document.text):
            break
        start = max(end - overlap, start + 1)
        index += 1
    return chunks

