from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.core.chroma_manager import ChromaManager
from app.db.database import Database
from app.api.models import ErrorResponse
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class CollectionStatsResponse(BaseModel):
    collection_name: str = Field(..., description="Name of the collection")
    document_count: int = Field(..., description="Number of documents in the collection")
    metadata: Dict[str, Any] = Field({}, description="Collection metadata")

class GlobalStatsResponse(BaseModel):
    total_collections: int = Field(..., description="Total number of collections")
    total_documents: int = Field(..., description="Total number of documents across all collections")
    collections: List[CollectionStatsResponse] = Field(..., description="Stats for each collection")
    vectorstore_info: Dict[str, Any] = Field({}, description="Information about the vectorstore")
    reconciliation_stats: Dict[str, Any] = Field({}, description="Statistics about reconciliation jobs")

@router.get(
    "",
    response_model=GlobalStatsResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_global_stats(
    chroma_manager: ChromaManager = Depends(),
    database: Database = Depends()
):
    """
    Get global statistics for the vectorstore service.
    """
    logger.info("Getting global statistics")
    try:
        # Get collection stats
        collections_info = []
        total_documents = 0
        collections = chroma_manager.list_collections()
        
        for collection in collections:
            count = chroma_manager.get_collection_count(collection.name)
            collections_info.append(
                CollectionStatsResponse(
                    collection_name=collection.name,
                    document_count=count,
                    metadata=collection.metadata or {}
                )
            )
            total_documents += count
        
        # Get reconciliation stats
        reconciliation_stats = {
            "total_jobs": database.get_reconciliation_job_count(),
            "completed_jobs": database.get_reconciliation_job_count(status="completed"),
            "failed_jobs": database.get_reconciliation_job_count(status="failed"),
            "running_jobs": database.get_reconciliation_job_count(status="running"),
            "last_24h_jobs": database.get_reconciliation_job_count(time_window_hours=24)
        }
        
        # Get vectorstore info
        vectorstore_info = chroma_manager.get_info()
        
        return GlobalStatsResponse(
            total_collections=len(collections),
            total_documents=total_documents,
            collections=collections_info,
            vectorstore_info=vectorstore_info,
            reconciliation_stats=reconciliation_stats
        )
    except Exception as e:
        logger.error(f"Unexpected error getting global stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get global stats: {str(e)}"
        )

@router.get(
    "/collections/{collection_name}",
    response_model=CollectionStatsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_collection_stats(
    collection_name: str,
    chroma_manager: ChromaManager = Depends()
):
    """
    Get statistics for a specific collection.
    """
    logger.info(f"Getting statistics for collection: {collection_name}")
    try:
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        
        count = chroma_manager.get_collection_count(collection_name)
        
        return CollectionStatsResponse(
            collection_name=collection_name,
            document_count=count,
            metadata=collection.metadata or {}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting collection stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection stats: {str(e)}"
        )
