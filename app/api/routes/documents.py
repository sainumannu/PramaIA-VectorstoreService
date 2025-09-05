from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any

from app.core.chroma_manager import ChromaManager
from app.api.models import (
    DocumentAddRequest,
    DocumentResponse,
    DocumentListResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
    ErrorResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)

@router.post(
    "/{collection_name}",
    response_model=DocumentListResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def add_documents(
    collection_name: str,
    request: DocumentAddRequest,
    chroma_manager: ChromaManager = Depends()
):
    """
    Add documents to a collection.
    """
    logger.info(f"Adding {len(request.documents)} documents to collection: {collection_name}")
    try:
        # Verify collection exists first
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        
        # Add documents to collection
        results = chroma_manager.add_documents(
            collection_name=collection_name,
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids,
            embeddings=request.embeddings
        )
        
        # Create response
        response_docs = []
        for i, doc_id in enumerate(results):
            response_docs.append(
                DocumentResponse(
                    id=doc_id,
                    document=request.documents[i] if i < len(request.documents) else None,
                    metadata=request.metadatas[i] if request.metadatas and i < len(request.metadatas) else None
                )
            )
        
        return DocumentListResponse(documents=response_docs)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents: {str(e)}"
        )

@router.get(
    "/{collection_name}",
    response_model=DocumentListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_documents(
    collection_name: str,
    ids: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    chroma_manager: ChromaManager = Depends()
):
    """
    Get documents from a collection.
    """
    logger.info(f"Getting documents from collection: {collection_name}")
    try:
        # Verify collection exists first
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        
        # Get documents
        results = chroma_manager.get_documents(
            collection_name=collection_name,
            ids=ids,
            limit=limit,
            offset=offset
        )
        
        # Create response
        response_docs = []
        for i, doc in enumerate(results):
            response_docs.append(
                DocumentResponse(
                    id=doc["id"],
                    document=doc.get("document"),
                    metadata=doc.get("metadata")
                )
            )
        
        return DocumentListResponse(documents=response_docs)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )

@router.post(
    "/{collection_name}/query",
    response_model=DocumentQueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def query_documents(
    collection_name: str,
    request: DocumentQueryRequest,
    chroma_manager: ChromaManager = Depends()
):
    """
    Query documents in a collection by text or embeddings.
    """
    logger.info(f"Querying documents in collection: {collection_name}")
    try:
        # Verify collection exists first
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        
        # Query documents
        results = chroma_manager.query_documents(
            collection_name=collection_name,
            query_texts=request.query_texts,
            query_embeddings=request.query_embeddings,
            n_results=request.n_results,
            where=request.where,
            where_document=request.where_document
        )
        
        # Process results
        processed_results = []
        for result in results:
            documents = []
            for i, doc_id in enumerate(result.get("ids", [])):
                documents.append(
                    DocumentResponse(
                        id=doc_id,
                        document=result.get("documents", [])[i] if result.get("documents") else None,
                        metadata=result.get("metadatas", [])[i] if result.get("metadatas") else None,
                        distance=result.get("distances", [])[i] if result.get("distances") else None
                    )
                )
            processed_results.append({"documents": documents})
        
        return DocumentQueryResponse(results=processed_results)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error querying documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
        )

@router.delete(
    "/{collection_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def delete_documents(
    collection_name: str,
    ids: List[str] = Query(..., description="IDs of documents to delete"),
    chroma_manager: ChromaManager = Depends()
):
    """
    Delete documents from a collection by IDs.
    """
    logger.info(f"Deleting documents from collection: {collection_name}")
    try:
        # Verify collection exists first
        collection = chroma_manager.get_collection(collection_name)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_name}"
            )
        
        # Delete documents
        success = chroma_manager.delete_documents(
            collection_name=collection_name,
            ids=ids
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete documents"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )
