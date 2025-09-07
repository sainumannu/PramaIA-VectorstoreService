"""
Collections module for Vectorstore Service.
"""

from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get("/")
async def get_collections():
    """
    Get collections.
    
    Returns:
        Dict: Collections information.
    """
    return {
        "message": "Collections endpoint operational",
        "collections": []
    }
