from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.core.chroma_manager import ChromaManager
from app.api.models import (
    CollectionCreateRequest, 
    CollectionResponse, 
    CollectionListResponse,
    ErrorResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/collections", tags=["collections"])
logger = get_logger(__name__)

@router.post(
    "", 
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        409: {"model": ErrorResponse, "description": "Collection already exists"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def create_collection(
    request: CollectionCreateRequest,
    chroma_manager: ChromaManager = Depends()
):
    """
    Create a new collection in the vectorstore.
    """
    logger.info(f"Creating collection: {request.name}")
    try:
        collection = chroma_manager.create_collection(
            name=request.name,
            metadata=request.metadata
        )
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            metadata=collection.metadata
        )
    except ValueError as e:
        logger.error(f"Collection creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Collection already exists: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )

@router.get(
    "", 
    response_model=CollectionListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def list_collections(
    chroma_manager: ChromaManager = Depends()
):
    """
    List all collections in the vectorstore.
    """
    logger.info("Listing all collections")
    try:
        collections = chroma_manager.list_collections()
        response = []
        for collection in collections:
            response.append(
                CollectionResponse(
                    id=collection.id,
                    name=collection.name,
                    metadata=collection.metadata
                )
            )
        return CollectionListResponse(collections=response)
    except Exception as e:
        logger.error(f"Unexpected error listing collections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )

@router.get(
    "/{collection_name}", 
    response_model=CollectionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_collection(
    collection_name: str,
    chroma_manager: ChromaManager = Depends()
):
    """
    Get a specific collection by name.
    """
    logger.info(f"Getting collection: {collection_name}")
    try:
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            metadata=collection.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )

@router.delete(
    "/{collection_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def delete_collection(
    collection_name: str,
    chroma_manager: ChromaManager = Depends()
):
    """
    Delete a collection by name.
    """
    logger.info(f"Deleting collection: {collection_name}")
    try:
        success = chroma_manager.delete_collection(collection_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )
