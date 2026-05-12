from fastapi import APIRouter

from app.api.v1.routes import documents, evaluations, query

api_router = APIRouter()
api_router.include_router(query.router, tags=["query"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(evaluations.router, tags=["evaluations"])

