"""
Statistics module for Vectorstore Service.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from app.utils.vectorstore_manager import VectorstoreManager

# Create router
router = APIRouter()

# Initialize VectorstoreManager
vectorstore_manager = VectorstoreManager()

@router.get("/")
async def get_stats():
    """
    Get statistics.
    
    Returns:
        Dict: Basic statistics.
    """
    stats = vectorstore_manager.get_stats()
    
    return {
        "message": "Stats endpoint operational",
        "status": "ok",
        "documents_total": stats.get("documents_total", 0),
        "documents_today": stats.get("documents_today", 0),
        "collections": stats.get("collections", 0),
        "processing_queue": stats.get("processing_queue", 0),
        "daily_stats": stats.get("daily_stats", [])
    }

@router.get("/processing")
async def get_processing_stats():
    """
    Get document processing statistics.
    
    Returns:
        Dict: Document processing statistics.
    """
    stats = vectorstore_manager.get_stats()
    documents = vectorstore_manager.get_documents()
    
    return {
        "documents_in_queue": stats.get("documents_in_queue", 0),
        "documents_in_coda": stats.get("processing_queue", 0),
        "documents_processed_today": stats.get("documents_today", 0),
        "total_documents": len(documents)
    }
