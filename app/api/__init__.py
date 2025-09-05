"""
Modulo API del VectorstoreService.
"""

from fastapi import APIRouter
from app.api.routes import documents, collections, reconciliation, health, stats, embeddings

# Create API router
api_router = APIRouter()

# Include all routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["reconciliation"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
