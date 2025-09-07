"""
Health check module for Vectorstore Service.
"""

from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get("/")
async def get_health():
    """
    Get health status.
    
    Returns:
        Dict: Health information.
    """
    return {
        "status": "ok"
    }
