from fastapi import APIRouter

from app.schemas.documents import DocumentIngestRequest, JobResponse
from app.workers.tasks import ingest_documents

router = APIRouter()


@router.post("/documents", response_model=JobResponse, status_code=202)
async def ingest_documents_endpoint(request: DocumentIngestRequest) -> JobResponse:
    task = ingest_documents.delay(request.model_dump())
    return JobResponse(job_id=task.id, status="queued")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    result = ingest_documents.AsyncResult(job_id)
    return JobResponse(job_id=job_id, status=result.status.lower())

