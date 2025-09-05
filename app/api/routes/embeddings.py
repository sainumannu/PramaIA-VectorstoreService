from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.chroma_manager import ChromaManager
from app.api.models import ErrorResponse
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to embed")

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(..., description="List of embeddings")

@router.post(
    "",
    response_model=EmbeddingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def create_embeddings(
    request: EmbeddingRequest,
    chroma_manager: ChromaManager = Depends()
):
    """
    Create embeddings for a list of texts.
    """
    logger.info(f"Creating embeddings for {len(request.texts)} texts")
    try:
        embeddings = chroma_manager.create_embeddings(request.texts)
        return EmbeddingResponse(embeddings=embeddings)
    except ValueError as e:
        logger.error(f"Invalid embedding request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid embedding request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create embeddings: {str(e)}"
        )
