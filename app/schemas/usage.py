from datetime import datetime
from pydantic import BaseModel, Field

class UsageLog(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    query_text: str
    answer_text: str
    tokens_used: int | None = None
    created_at: datetime
    
class UsageResponse(BaseModel):
    logs: list[UsageLog]
    total_queries: int
    total_tokens: int | None = None
