from fastapi import APIRouter

from app.api.v1.routes import admin, auth, documents, evaluations, history, query

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(query.router, tags=["query"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(evaluations.router, tags=["evaluations"])
api_router.include_router(history.router)
