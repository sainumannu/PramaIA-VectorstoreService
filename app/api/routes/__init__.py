from fastapi import APIRouter

from app.api.routes import collections, documents, reconciliation, health

api_router = APIRouter()

api_router.include_router(collections.router)
api_router.include_router(documents.router)
api_router.include_router(reconciliation.router)
api_router.include_router(health.router)

# Add any other routers here
