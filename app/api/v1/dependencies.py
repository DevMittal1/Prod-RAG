from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.db.mongodb import get_db
from app.db.s3 import get_s3_client
from app.guardrails.policy import GuardrailService
from app.memory.redis_memory import RedisMemoryStore
from app.observability.langfuse_client import LangfuseTracer
from app.rag.embeddings import GeminiEmbeddingService
from app.rag.llm import GeminiLLMGateway
from app.rag.pipeline import RAGPipeline
from app.rag.rerankers import Reranker
from app.rag.retrievers import HybridRetriever

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # In a real app we'd fetch the user from MongoDB here
    return {"id": user_id}

@lru_cache
def get_rag_pipeline() -> RAGPipeline:
    settings = get_settings()
    return RAGPipeline(
        settings=settings,
        embeddings=GeminiEmbeddingService(settings),
        retriever=HybridRetriever(settings=settings),
        reranker=Reranker(),
        llm=GeminiLLMGateway(settings),
        memory=RedisMemoryStore(settings.redis_url),
        guardrails=GuardrailService(),
        tracer=LangfuseTracer(settings),
    )
