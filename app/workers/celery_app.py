from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "production_rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.ingest_documents": {"queue": "ingestion"},
    },
)

