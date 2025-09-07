"""
Statistics module for Vectorstore Service.
"""

from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get("/")
async def get_stats():
    """
    Get statistics.
    
    Returns:
        Dict: Basic statistics.
    """
    return {
        "message": "Stats endpoint operational",
        "status": "ok"
    }
