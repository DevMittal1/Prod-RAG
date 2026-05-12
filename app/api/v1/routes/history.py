from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_db
from app.schemas.usage import UsageResponse, UsageLog

router = APIRouter(prefix="/history", tags=["history"])

@router.get("", response_model=UsageResponse)
async def get_history(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user["id"]
    cursor = db.usage_logs.find({"user_id": user_id}).sort("created_at", -1)
    
    logs = []
    total_tokens = 0
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(UsageLog(**doc))
        if doc.get("tokens_used"):
            total_tokens += doc["tokens_used"]
            
    return UsageResponse(
        logs=logs,
        total_queries=len(logs),
        total_tokens=total_tokens
    )

@router.delete("/{log_id}")
async def delete_history_item(log_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    from bson import ObjectId
    user_id = current_user["id"]
    
    try:
        obj_id = ObjectId(log_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid log ID format")

    result = await db.usage_logs.delete_one({"_id": obj_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Log not found")
        
    return {"status": "success"}
