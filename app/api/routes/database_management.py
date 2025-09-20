"""
API routes per la gestione del database documenti e vector store.
Aggiunge gli endpoint necessari per supportare i nuovi componenti frontend.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import os
import logging
import json
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.utils.document_database import DocumentDatabase
from app.utils.extended_vectorstore_manager import ExtendedVectorstoreManager

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione del router
router = APIRouter(prefix="/api/database-management", tags=["database"])

# Inizializzazione delle dipendenze
doc_db = DocumentDatabase()
vector_manager = ExtendedVectorstoreManager()

# Directory per i backup
BACKUP_DIR = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Utility function per ottenere la dimensione del file
def get_file_size(file_path: str) -> int:
    """Ottiene la dimensione di un file in bytes."""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Errore nel calcolo della dimensione del file {file_path}: {str(e)}")
        return 0

# Utility function per creare un timestamp formattato
def get_timestamp() -> str:
    """Restituisce un timestamp formattato per i nomi dei backup."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Endpoint per ottenere lo stato del database documenti
@router.get("/documents/status")
async def get_document_db_status():
    """
    Restituisce lo stato e le statistiche del database documenti.
    """
    try:
        # Ottieni il conteggio totale dei documenti
        total_documents = doc_db.get_document_count()
        
        # Calcola dimensione del database
        db_path = doc_db.db_file
        db_size = get_file_size(db_path)
        
        # Ottieni statistiche
        stats = doc_db.get_collection_stats()
        
        # Calcola il numero di documenti aggiunti oggi
        # Utilizziamo una query SQL diretta per questioni di performance
        conn = doc_db._get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE created_at LIKE ?",
            (f"{today}%",)
        )
        documents_today = cursor.fetchone()[0]
        
        # Calcola dimensione media documento
        if total_documents > 0:
            avg_document_size = round(db_size / total_documents / 1024, 2)  # in KB
        else:
            avg_document_size = 0
        
        conn.close()
        
        return {
            "status": "ok",
            "total_documents": total_documents,
            "documents_today": documents_today,
            "size_bytes": db_size,
            "avg_document_size": avg_document_size,
            "collections": stats.get("collections", {}),
            "latest_document": stats.get("latest_document"),
            "database_path": db_path
        }
    except Exception as e:
        logger.error(f"Errore nel recupero dello stato del database documenti: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Endpoint per elencare i documenti
@router.get("/documents/list")
async def list_documents(limit: int = 100, offset: int = 0):
    """
    Restituisce la lista dei documenti nel database.
    """
    try:
        # Ottieni documenti
        documents = doc_db.get_documents(limit=limit, offset=offset)
        total = doc_db.get_document_count()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "documents": documents,
            "message": f"Mostrati {len(documents)} di {total} documenti"
        }
    except Exception as e:
        logger.error(f"Errore nel recupero della lista documenti: {str(e)}")
        return {
            "error": str(e),
            "documents": []
        }

# Endpoint per il backup del database documenti
@router.post("/documents/backup")
async def backup_document_db(background_tasks: BackgroundTasks):
    """
    Crea un backup del database documenti.
    """
    try:
        # Crea directory di backup specifica
        backup_path = os.path.join(BACKUP_DIR, f"documents_backup_{get_timestamp()}")
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup del database SQLite
        db_source = doc_db.db_file
        db_dest = os.path.join(backup_path, "documents.db")
        
        # Utilizziamo la funzione esporta in JSON per un backup secondario
        json_dest = os.path.join(backup_path, "documents.json")
        
        # Esegui il backup in background
        def do_backup():
            try:
                # Copia il file del database
                shutil.copy2(db_source, db_dest)
                
                # Esporta anche in JSON
                doc_db.export_to_json(json_dest)
                
                logger.info(f"Backup del database documenti completato: {backup_path}")
            except Exception as e:
                logger.error(f"Errore durante l'esecuzione del backup in background: {str(e)}")
        
        background_tasks.add_task(do_backup)
        
        return {
            "success": True,
            "message": "Backup del database documenti avviato",
            "details": {
                "backup_path": backup_path
            }
        }
    except Exception as e:
        logger.error(f"Errore nell'avvio del backup del database documenti: {str(e)}")
        return {
            "success": False,
            "message": f"Errore nel backup: {str(e)}"
        }

# Endpoint per il reset del database documenti
@router.post("/documents/reset")
async def reset_document_db():
    """
    Resetta il database documenti (elimina tutti i documenti).
    """
    try:
        # Crea un backup prima del reset
        backup_path = os.path.join(BACKUP_DIR, f"documents_pre_reset_{get_timestamp()}")
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup del database e JSON
        db_source = doc_db.db_file
        db_dest = os.path.join(backup_path, "documents.db")
        json_dest = os.path.join(backup_path, "documents.json")
        
        # Copia il file del database
        shutil.copy2(db_source, db_dest)
        
        # Esporta anche in JSON
        doc_db.export_to_json(json_dest)
        
        # Elimina il database attuale
        try:
            os.remove(db_source)
        except:
            pass
        
        # Reinizializza il database (nuovo vuoto)
        # Utilizziamo una variabile temporanea e poi la assegnamo alla variabile globale
        # all'esterno di questa funzione
        temp_db = DocumentDatabase(migrate_from_json=False)
        
        # Aggiorniamo il riferimento globale al database
        globals()['doc_db'] = temp_db
        
        return {
            "success": True,
            "message": "Database documenti resettato con successo",
            "details": {
                "backup_path": backup_path
            }
        }
    except Exception as e:
        logger.error(f"Errore nel reset del database documenti: {str(e)}")
        return {
            "success": False,
            "message": f"Errore nel reset: {str(e)}"
        }

# Endpoint per ottenere lo stato del vector store
@router.get("/vectorstore/status")
async def get_vectorstore_status():
    """
    Restituisce lo stato e le statistiche del vector store.
    """
    try:
        # Ottieni informazioni dal vector store
        stats = vector_manager.get_statistics()
        
        # Aggiungi informazioni aggiuntive specifiche
        today = datetime.now().strftime("%Y-%m-%d")
        documents_today = 0
        
        # Ottieni i documenti del vector store per contare quelli di oggi
        try:
            all_docs = vector_manager.list_documents(metadata_only=True)
            for doc in all_docs:
                if doc.get("metadata", {}).get("ingest_time", "").startswith(today):
                    documents_today += 1
        except Exception as vs_error:
            logger.warning(f"Errore nel conteggio dei documenti odierni: {str(vs_error)}")
        
        return {
            "status": "ok",
            "documents_in_index": stats.get("total_documents", 0),
            "collections": stats.get("collections", []),
            "documents_today": documents_today,
            "avg_chunk_size": stats.get("avg_chunk_size", 0),
            "embedding_model": stats.get("embedding_model", ""),
            "database_path": vector_manager.get_persistence_path()
        }
    except Exception as e:
        logger.error(f"Errore nel recupero dello stato del vector store: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Endpoint per elencare i documenti nel vector store
@router.get("/vectorstore/documents")
async def list_vectorstore_documents(limit: int = 20, offset: int = 0):
    """
    Restituisce la lista dei documenti nel vector store.
    """
    try:
        # Ottieni i documenti
        documents = vector_manager.list_documents(limit=limit, offset=offset)
        total_count = vector_manager.get_document_count()
        
        # Trasforma in formato più adatto alla visualizzazione
        formatted_docs = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            formatted_doc = {
                "id": doc.get("id", ""),
                "source_filename": metadata.get("source", "Sconosciuto"),
                "page": metadata.get("page", "N/A"),
                "ingest_time": metadata.get("ingest_time", "N/A"),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "metadata": metadata
            }
            formatted_docs.append(formatted_doc)
        
        return {
            "total": total_count,
            "documents": formatted_docs,
            "message": f"Mostrati {len(formatted_docs)} di {total_count} documenti"
        }
    except Exception as e:
        logger.error(f"Errore nel recupero dei documenti dal vector store: {str(e)}")
        return {
            "error": str(e),
            "documents": []
        }

# Endpoint per il backup del vector store
@router.post("/vectorstore/backup")
async def backup_vectorstore(background_tasks: BackgroundTasks):
    """
    Crea un backup del vector store.
    """
    try:
        # Crea directory di backup specifica
        backup_path = os.path.join(BACKUP_DIR, f"vectorstore_backup_{get_timestamp()}")
        os.makedirs(backup_path, exist_ok=True)
        
        # Ottieni il percorso del database di ChromaDB
        chroma_path = vector_manager.get_persistence_path()
        
        # Esegui il backup in background
        def do_backup():
            try:
                # Copia la directory di ChromaDB
                if os.path.isdir(chroma_path):
                    chroma_dest = os.path.join(backup_path, "chroma_db")
                    shutil.copytree(chroma_path, chroma_dest)
                    
                    # Esporta anche metadati in JSON
                    try:
                        documents = vector_manager.list_documents(metadata_only=True)
                        with open(os.path.join(backup_path, "vector_documents.json"), "w", encoding="utf-8") as f:
                            json.dump({"documents": documents}, f, ensure_ascii=False, indent=2)
                    except Exception as json_err:
                        logger.warning(f"Errore nell'esportazione JSON del vector store: {str(json_err)}")
                    
                    logger.info(f"Backup del vector store completato: {backup_path}")
                else:
                    raise ValueError(f"Il percorso del vector store non è valido: {chroma_path}")
            except Exception as e:
                logger.error(f"Errore durante l'esecuzione del backup del vector store: {str(e)}")
        
        background_tasks.add_task(do_backup)
        
        return {
            "success": True,
            "message": "Backup del vector store avviato",
            "details": {
                "backup_path": backup_path,
                "source_path": chroma_path
            }
        }
    except Exception as e:
        logger.error(f"Errore nell'avvio del backup del vector store: {str(e)}")
        return {
            "success": False,
            "message": f"Errore nel backup: {str(e)}"
        }

# Endpoint per il reset del vector store
@router.post("/vectorstore/reset")
async def reset_vectorstore():
    """
    Resetta il vector store (elimina tutti i documenti).
    """
    try:
        # Crea un backup prima del reset
        backup_path = os.path.join(BACKUP_DIR, f"vectorstore_pre_reset_{get_timestamp()}")
        os.makedirs(backup_path, exist_ok=True)
        
        # Ottieni il percorso del database di ChromaDB
        chroma_path = vector_manager.get_persistence_path()
        
        # Esegui backup
        if os.path.isdir(chroma_path):
            chroma_dest = os.path.join(backup_path, "chroma_db")
            shutil.copytree(chroma_path, chroma_dest)
            
            # Esporta anche metadati in JSON
            try:
                documents = vector_manager.list_documents(metadata_only=True)
                with open(os.path.join(backup_path, "vector_documents.json"), "w", encoding="utf-8") as f:
                    json.dump({"documents": documents}, f, ensure_ascii=False, indent=2)
            except Exception as json_err:
                logger.warning(f"Errore nell'esportazione JSON del vector store: {str(json_err)}")
        
        # Resetta il vector store
        success = vector_manager.reset()
        
        if success:
            return {
                "success": True,
                "message": "Vector store resettato con successo",
                "details": {
                    "backup_path": backup_path
                }
            }
        else:
            return {
                "success": False,
                "message": "Errore nel reset del vector store"
            }
    except Exception as e:
        logger.error(f"Errore nel reset del vector store: {str(e)}")
        return {
            "success": False,
            "message": f"Errore nel reset: {str(e)}"
        }
