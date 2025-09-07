"""
Documents module for Vectorstore Service.
"""

from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get("/")
async def get_documents():
    """
    Get documents.
    
    Returns:
        Dict: Documents information.
    """
    return {
        "message": "Documents endpoint operational",
        "documents": []
    }
