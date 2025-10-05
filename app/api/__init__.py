"""
Modulo API del VectorstoreService.
"""

from fastapi import APIRouter
from app.api.routes import documents, collections, reconciliation, health, stats, embeddings, api_gateway, vectorstore, settings, database, database_management, vectorstore_service_status, file_hashes

# Create API router
api_router = APIRouter()

# Include all routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["reconciliation"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(vectorstore.router, prefix="/vectorstore", tags=["vectorstore"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

# Gateway API per compatibilità frontend
api_router.include_router(api_gateway.router, prefix="/api/database-management", tags=["api-gateway"])

# API per la gestione del database
api_router.include_router(database.router, prefix="/api/v1", tags=["database-admin"])

# API per la gestione della UI database
api_router.include_router(database_management.router, tags=["database-management"])

# API per lo stato del servizio Vectorstore
api_router.include_router(vectorstore_service_status.router, tags=["vectorstore-status"])

# API per la gestione degli hash dei file
api_router.include_router(file_hashes.router, tags=["file-hashes"])

# Ensure api_router is exported
__all__ = ["api_router"]
