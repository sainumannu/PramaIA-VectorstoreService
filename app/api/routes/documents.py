
# ...existing code...

"""
Documents module for Vectorstore Service.
"""

from fastapi import APIRouter, HTTPException, Body, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.utils.document_manager import DocumentManager

# Create router
router = APIRouter()

# DocumentManager globale (inizializzato lazy)
metadata_manager = None

def get_metadata_manager():
    """Inizializza il DocumentManager in modo lazy."""
    global metadata_manager
    if metadata_manager is None:
        try:
            print("[DEBUG] Inizializzazione DocumentManager...")
            metadata_manager = DocumentManager()
            print("[DEBUG] DocumentManager inizializzato con successo")
        except Exception as e:
            print(f"[ERROR] Errore inizializzazione DocumentManager: {e}")
            import traceback
            traceback.print_exc()
            raise
    return metadata_manager

# Endpoint per ricalcolo statistiche
@router.post("/recalculate-stats")
async def recalculate_stats():
    """
    Ricalcola le statistiche dei documenti in base ai dati attuali.
    """
    # Usa sync_databases invece di recalculate_stats
    manager = get_metadata_manager()
    result = manager.sync_databases()
    if not result.get('success', False):
        raise HTTPException(
            status_code=500,
            detail="Errore durante il ricalcolo delle statistiche"
        )
    return {"message": "Statistiche ricalcolate correttamente", "details": result}

@router.get("/")
async def get_documents(limit: int = 50, offset: int = 0):
    """
    Get all documents with pagination.
    
    Args:
        limit: Number of documents to return (default: 50)
        offset: Number of documents to skip (default: 0)
    
    Returns:
        Dict: Documents information with pagination.
    """
    print(f"[DEBUG] Chiamata endpoint /documents/ con limit={limit}, offset={offset}")
    
    try:
        print(f"[DEBUG] Tentativo lista documenti da SQLite...")
        # Prima prova a ottenere documenti da SQLite
        manager = get_metadata_manager()
        all_doc_ids = manager.list_all_documents()
        print(f"[DEBUG] SQLite ha restituito {len(all_doc_ids)} IDs: {all_doc_ids[:5]}")
        
        # Se SQLite è vuoto, leggi direttamente da ChromaDB
        if not all_doc_ids:
            print(f"[DEBUG] SQLite vuoto, tentativo lettura ChromaDB...")
            try:
                collection = manager.vector_db.get_collection()
                if collection:
                    print(f"[DEBUG] Collezione ChromaDB trovata")
                    chroma_data = collection.get()
                    all_doc_ids = chroma_data.get('ids', []) if chroma_data else []
                    print(f"[DEBUG] ChromaDB ha restituito {len(all_doc_ids)} IDs")
                else:
                    print(f"[DEBUG] Nessuna collezione ChromaDB trovata")
            except Exception as e:
                print(f"[DEBUG] Errore lettura ChromaDB: {e}")
                all_doc_ids = []
        
        print(f"[DEBUG] Applicazione paginazione: offset={offset}, limit={limit}")
        # Apply pagination
        paginated_ids = all_doc_ids[offset:offset + limit]
        print(f"[DEBUG] IDs paginati: {paginated_ids}")
        
        print(f"[DEBUG] Recupero dettagli documenti...")
        # Get detailed document information for paginated results
        documents = []
        for i, doc_id in enumerate(paginated_ids):
            print(f"[DEBUG] Elaborazione documento {i+1}/{len(paginated_ids)}: {doc_id}")
            try:
                # Prima prova SQLite
                doc = manager.get_document(doc_id)
                print(f"[DEBUG] SQLite per {doc_id}: {'trovato' if doc else 'non trovato'}")
                
                # Se non trovato in SQLite, prova ChromaDB
                if not doc:
                    print(f"[DEBUG] Tentativo ChromaDB per {doc_id}")
                    try:
                        collection = manager.vector_db.get_collection()
                        if collection:
                            chroma_data = collection.get(ids=[doc_id])
                            if chroma_data and chroma_data.get('documents'):
                                doc = {
                                    'id': doc_id,
                                    'content': chroma_data['documents'][0] if chroma_data['documents'] else '',
                                    'metadata': chroma_data['metadatas'][0] if chroma_data.get('metadatas') and chroma_data['metadatas'] else {}
                                }
                                print(f"[DEBUG] ChromaDB per {doc_id}: documento ricostruito")
                    except Exception as e:
                        print(f"[DEBUG] Errore lettura documento {doc_id} da ChromaDB: {e}")
                
                if doc:
                    documents.append(doc)
                    print(f"[DEBUG] Documento {doc_id} aggiunto alla lista")
                    
            except Exception as e:
                print(f"[DEBUG] Errore elaborazione documento {doc_id}: {e}")
                continue
        
        print(f"[DEBUG] Preparazione risposta finale...")
        result = {
            "message": "Documents endpoint operational",
            "documents": documents,
            "total": len(all_doc_ids),
            "limit": limit,
            "offset": offset,
            "returned": len(documents)
        }
        print(f"[DEBUG] Risposta pronta: {len(documents)} documenti restituiti")
        return result
        
    except Exception as e:
        print(f"[ERROR] Errore generale endpoint documents: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message": "Documents endpoint operational",
            "documents": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "returned": 0,
            "error": str(e)
        }

@router.get("/list")
async def list_documents():
    """
    Get list of documents.
    
    Returns:
        Dict: List of document IDs.
    """
    document_ids = get_metadata_manager().list_all_documents()
    return {
        "documents": document_ids,
        "total": len(document_ids)
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
    try:
        # Genera un ID per il documento se non è presente
        if "id" not in document:
            document["id"] = f"doc{uuid.uuid4().hex[:8]}"
        
        # Aggiungi timestamp di creazione se non presente
        if "metadata" not in document:
            document["metadata"] = {}
        
        if "created_at" not in document["metadata"]:
            document["metadata"]["created_at"] = datetime.now().isoformat()
        
        print(f"Aggiunta documento con ID: {document['id']}")
        print(f"Collezione: {document.get('collection', 'default')}")
        print(f"Contenuto lunghezza: {len(document.get('content', '')) if 'content' in document else 'Nessun contenuto'}")
        
        # Salva il documento con i parametri corretti
        doc_id = document.get('id', str(uuid.uuid4()))
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        success = get_metadata_manager().add_document(doc_id, content, metadata)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il salvataggio del documento"
            )
        
        # Verifica se il documento è stato effettivamente salvato
        saved_doc = get_metadata_manager().get_document(document["id"])
        if not saved_doc:
            print(f"AVVISO: Documento {document['id']} non trovato dopo il salvataggio")
        else:
            print(f"Documento {document['id']} salvato con successo. Contenuto: {len(saved_doc.get('content', '')) if 'content' in saved_doc else 'Nessun contenuto'}")
        
        return document
    except Exception as e:
        print(f"Errore nell'aggiunta del documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il salvataggio del documento: {str(e)}"
        )

@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document.
    
    Args:
        document_id: ID of the document to retrieve.
        
    Returns:
        Dict: Document information.
    """
    document = get_metadata_manager().get_document(document_id)
    
    # Log debug info
    print(f"Richiesto documento con ID: {document_id}")
    print(f"Documento trovato: {document is not None}")
    
    if not document:
        # Verifica se esistono documenti nel database (per diagnostica)
        try:
            all_doc_ids = get_metadata_manager().list_all_documents()
            first_5_ids = all_doc_ids[:5]
            print(f"Documento {document_id} non trovato. Primi 5 documenti disponibili: {first_5_ids}")
            
            # Verifica se il documento esiste in ChromaDB
            from app.core.vectordb_manager import VectorDBManager
            chroma = VectorDBManager()
            collection = chroma.get_collection("test_documents")
            
            if collection:
                try:
                    chroma_docs = collection.get(ids=[document_id])
                    if chroma_docs and chroma_docs.get("ids"):
                        print(f"Documento {document_id} trovato in ChromaDB ma non nel database")
                        
                        # Recupera il contenuto da ChromaDB
                        content = ""
                        if "documents" in chroma_docs and chroma_docs["documents"] and len(chroma_docs["documents"]) > 0:
                            if len(chroma_docs["documents"][0]) > 0:
                                content = chroma_docs["documents"][0][0]
                            
                        # Recupera i metadati
                        metadata_dict = {}
                        if "metadatas" in chroma_docs and chroma_docs["metadatas"] and len(chroma_docs["metadatas"]) > 0:
                            if len(chroma_docs["metadatas"][0]) > 0:
                                metadata_dict = chroma_docs["metadatas"][0][0]
                                if not isinstance(metadata_dict, dict):
                                    metadata_dict = {}
                        
                        # Crea un documento sintetico
                        print(f"Creazione documento sintetico da ChromaDB")
                        filename = f"document_{document_id}"
                        collection = "test_documents"
                        
                        if isinstance(metadata_dict, dict):
                            if "filename" in metadata_dict:
                                filename = metadata_dict["filename"]
                            if "collection" in metadata_dict:
                                collection = metadata_dict["collection"]
                        
                        document = {
                            "id": document_id,
                            "filename": filename,
                            "collection": collection,
                            "content": content,
                            "metadata": metadata_dict
                        }
                        
                        # Salva il documento nel database per future richieste
                        get_metadata_manager().add_document(document_id, content, metadata_dict)
                        print(f"Documento {document_id} recuperato da ChromaDB e salvato nel database")
                        
                        return document
                except Exception as e:
                    print(f"Errore nel recupero da ChromaDB: {str(e)}")
        except Exception as list_err:
            print(f"Errore nell'elencare i documenti disponibili: {str(list_err)}")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato"
        )
    
    # Se troviamo il documento, verifichiamo che abbia contenuto
    if "content" in document and document["content"]:
        print(f"Documento {document_id} ha contenuto di {len(document['content'])} caratteri")
    else:
        print(f"Documento {document_id} non ha contenuto nel campo 'content'")
    
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
    success = get_metadata_manager().delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato"
        )
    
    return {"message": f"Documento con ID {document_id} eliminato con successo"}
