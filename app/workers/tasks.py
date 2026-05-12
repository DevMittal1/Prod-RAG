import structlog

from app.core.config import get_settings
from app.ingestion.chunking import chunk_document
from app.ingestion.indexer import DocumentIndexer
from app.schemas.documents import DocumentIngestRequest
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_documents(self, payload: dict) -> dict[str, int | str]:
    request = DocumentIngestRequest.model_validate(payload)
    settings = get_settings()
    indexer = DocumentIndexer(settings)

    chunks = []
    for document in request.documents:
        enriched = document.model_copy(
            update={"metadata": {**document.metadata, "tenant_id": request.tenant_id}}
        )
        chunks.extend(
            chunk_document(
                enriched,
                chunk_size=settings.document_chunk_size,
                overlap=settings.document_chunk_overlap,
            )
        )

    indexed = indexer.index(chunks)
    logger.info("documents_indexed", tenant_id=request.tenant_id, indexed=indexed)
    return {"tenant_id": request.tenant_id, "indexed": indexed}
