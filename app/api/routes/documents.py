
# ...existing code...

"""
Documents module for Vectorstore Service.
"""

from fastapi import APIRouter, HTTPException, Body, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.utils.vectorstore_manager_db import VectorstoreManager

# Create router
router = APIRouter()

# Endpoint per ricalcolo statistiche
@router.post("/recalculate-stats")
async def recalculate_stats():
    """
    Ricalcola le statistiche dei documenti in base ai dati attuali.
    """
    success = vectorstore_manager.recalculate_stats()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Errore durante il ricalcolo delle statistiche"
        )
    return {"message": "Statistiche ricalcolate correttamente"}
# Initialize VectorstoreManager
vectorstore_manager = VectorstoreManager()

@router.get("/")
async def get_documents():
    """
    Get all documents.
    
    Returns:
        Dict: Documents information.
    """
    documents = vectorstore_manager.get_documents()
    return {
        "message": "Documents endpoint operational",
        "documents": documents
    }

@router.get("/list")
async def list_documents():
    """
    Get list of documents.
    
    Returns:
        Dict: List of documents.
    """
    documents = vectorstore_manager.get_documents()
    return {
        "documents": documents
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(document: Dict[str, Any] = Body(...)):
    """
    Create a new document.
    
    Args:
        document: Document data.
        
    Returns:
        Dict: Created document.
    """
    # Genera un ID per il documento se non è presente
    if "id" not in document:
        document["id"] = f"doc{uuid.uuid4().hex[:8]}"
    
    # Aggiungi timestamp di creazione se non presente
    if "metadata" not in document:
        document["metadata"] = {}
    
    if "created_at" not in document["metadata"]:
        document["metadata"]["created_at"] = datetime.now().isoformat()
    
    # Salva il documento
    success = vectorstore_manager.add_document(document)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il salvataggio del documento"
        )
    
    return document

@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document.
    
    Args:
        document_id: ID of the document to retrieve.
        
    Returns:
        Dict: Document information.
    """
    document = vectorstore_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato"
        )
    
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    
    Args:
        document_id: ID of the document to delete.
        
    Returns:
        Dict: Deletion confirmation.
    """
    success = vectorstore_manager.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato"
        )
    
    return {"message": f"Documento con ID {document_id} eliminato con successo"}
