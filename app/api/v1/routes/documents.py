from datetime import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from bson import ObjectId

from app.api.v1.dependencies import get_current_user
from app.core.config import get_settings
from app.db.mongodb import get_db
from app.db.s3 import get_s3_client
from app.schemas.documents import DocumentIngestRequest, JobResponse, DocumentMetadataResponse, DocumentListResponse
from app.workers.tasks import ingest_documents

router = APIRouter(prefix="/documents")


@router.post("/ingest", response_model=JobResponse, status_code=202)
async def ingest_documents_endpoint(request: DocumentIngestRequest, current_user: dict = Depends(get_current_user)) -> JobResponse:
    # Adding current_user dependency to ensure only authenticated users can trigger ingestion
    task = ingest_documents.delay(request.model_dump())
    return JobResponse(job_id=task.id, status="queued")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)) -> JobResponse:
    result = ingest_documents.AsyncResult(job_id)
    return JobResponse(job_id=job_id, status=result.status.lower())


@router.post("/upload", response_model=DocumentMetadataResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    s3_client=Depends(get_s3_client)
):
    settings = get_settings()
    user_id = current_user["id"]
    
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    s3_key = f"{user_id}/{uuid.uuid4()}.{file_extension}"
    
    # Read file content
    content = await file.read()
    
    # Upload to S3
    await s3_client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Body=content,
        ContentType=file.content_type or "application/octet-stream"
    )
    
    # Save metadata to MongoDB
    doc = {
        "user_id": user_id,
        "filename": file.filename,
        "s3_key": s3_key,
        "content_type": file.content_type,
        "size": len(content),
        "created_at": datetime.utcnow().isoformat()
    }
    result = await db.documents.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    
    return DocumentMetadataResponse(**doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user["id"]
    cursor = db.documents.find({"user_id": user_id}).sort("created_at", -1)
    
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(DocumentMetadataResponse(**doc))
        
    return DocumentListResponse(documents=docs)


@router.get("/{doc_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(doc_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user["id"]
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
        
    doc = await db.documents.find_one({"_id": obj_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc["_id"] = str(doc["_id"])
    return DocumentMetadataResponse(**doc)


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    s3_client=Depends(get_s3_client)
):
    settings = get_settings()
    user_id = current_user["id"]
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
        
    doc = await db.documents.find_one({"_id": obj_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        response = await s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=doc["s3_key"]
        )
        
        async def content_stream():
            async for chunk in response['Body']:
                yield chunk
                
        return StreamingResponse(
            content_stream(),
            media_type=doc.get("content_type", "application/octet-stream"),
            headers={"Content-Disposition": f"inline; filename={doc['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from storage: {str(e)}")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
    s3_client=Depends(get_s3_client)
):
    settings = get_settings()
    user_id = current_user["id"]
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
        
    doc = await db.documents.find_one({"_id": obj_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from S3
    try:
        await s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=doc["s3_key"]
        )
    except Exception as e:
        # We'll log it but still try to delete from DB
        print(f"Failed to delete object from S3: {e}")
        
    # Delete from MongoDB
    await db.documents.delete_one({"_id": obj_id})
    
    return {"status": "success", "message": "Document deleted"}

