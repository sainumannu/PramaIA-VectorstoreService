"""
Modulo per la gestione della riconciliazione tra filesystem e vectorstore.
"""

import os
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
import asyncio
import time

from app.core.chroma_manager import get_chroma_manager
from app.db.database import get_db
from app.utils.config import get_settings

# Configurazione logging
logger = logging.getLogger(__name__)

class ReconciliationService:
    """Servizio per la riconciliazione tra filesystem e vectorstore."""
    
    def __init__(self):
        """Inizializza il servizio di riconciliazione."""
        self.db = get_db()
        self.chroma_manager = get_chroma_manager()
        self.supported_extensions = {".pdf", ".txt", ".md", ".json", ".csv"}
    
    async def start_reconciliation(self, delete_missing: bool = True, batch_size: int = 1000) -> int:
        """
        Avvia un job di riconciliazione.
        
        Args:
            delete_missing: Se eliminare i documenti presenti nel vectorstore ma non nel filesystem
            batch_size: Dimensione del batch per l'elaborazione
            
        Returns:
            ID del job creato
        """
        try:
            # Crea il job nel database
            job_id = await self.db.create_job(delete_missing, batch_size)
            
            # Avvia il processo di riconciliazione in modo asincrono
            asyncio.create_task(self._run_reconciliation(job_id, delete_missing, batch_size))
            
            return job_id
            
        except Exception as e:
            logger.error(f"Errore avvio riconciliazione: {str(e)}")
            raise
    
    async def _run_reconciliation(self, job_id: int, delete_missing: bool, batch_size: int):
        """
        Esegue il processo di riconciliazione.
        
        Args:
            job_id: ID del job
            delete_missing: Se eliminare i documenti presenti nel vectorstore ma non nel filesystem
            batch_size: Dimensione del batch per l'elaborazione
        """
        start_time = time.time()
        
        try:
            # Ottieni directory monitorate
            monitored_dirs = await self._get_monitored_directories()
            
            if not monitored_dirs:
                error_msg = "Nessuna directory monitorata trovata"
                logger.error(error_msg)
                await self.db.update_job(
                    job_id=job_id,
                    status="failed",
                    end_time=datetime.now().isoformat(),
                    error_message=error_msg
                )
                return
            
            # Scansiona filesystem
            logger.info(f"Scansione filesystem per job {job_id}")
            files_info = await self._scan_filesystem(monitored_dirs)
            
            # Aggiorna job con totale file
            await self.db.update_job(
                job_id=job_id,
                total_files=len(files_info)
            )
            
            # Ottieni collezione ChromaDB
            collection_name = get_settings().default_collection_name
            
            # Riconcilia vectorstore con filesystem
            logger.info(f"Riconciliazione per job {job_id} - {len(files_info)} file trovati")
            
            added_count, updated_count, removed_count, error_count = await self._reconcile_vectorstore(
                job_id=job_id,
                files_info=files_info,
                collection_name=collection_name,
                delete_missing=delete_missing,
                batch_size=batch_size
            )
            
            # Aggiorna statistiche del job
            duration = time.time() - start_time
            
            await self.db.update_job(
                job_id=job_id,
                status="completed",
                end_time=datetime.now().isoformat(),
                processed_files=len(files_info),
                added_files=added_count,
                updated_files=updated_count,
                removed_files=removed_count,
                errors=error_count
            )
            
            # Aggiorna statistiche globali
            await self.db.update_stats("last_reconciliation", datetime.now().isoformat())
            await self.db.update_stats("last_reconciliation_duration", str(round(duration, 2)))
            await self.db.update_stats("last_reconciliation_files", str(len(files_info)))
            await self.db.update_stats("total_documents", str(len(files_info)))
            
            logger.info(f"Riconciliazione completata per job {job_id}: {added_count} aggiunti, {updated_count} aggiornati, {removed_count} rimossi, {error_count} errori in {round(duration, 2)} secondi")
            
        except Exception as e:
            error_msg = f"Errore durante la riconciliazione: {str(e)}"
            logger.error(error_msg)
            
            await self.db.update_job(
                job_id=job_id,
                status="failed",
                end_time=datetime.now().isoformat(),
                error_message=error_msg
            )
    
    async def _get_monitored_directories(self) -> List[str]:
        """
        Ottiene l'elenco delle directory monitorate dal PDF Monitor Agent.
        
        Returns:
            Lista di percorsi di directory monitorate
        """
        # In una implementazione reale, dovremmo chiamare un'API o consultare un database
        # per ottenere le directory monitorate.
        # Per ora, utilizziamo un valore di esempio o leggiamo da configurazione
        
        # TODO: Implementare chiamata API al PDF Monitor Agent
        
        # Esempio di directory monitorate
        monitored_dirs = [
            "C:/Documenti",
            "C:/Progetti"
        ]
        
        # Se non ci sono directory configurate, usa una directory di test
        if not monitored_dirs:
            test_dir = os.path.join(os.getcwd(), "test_files")
            os.makedirs(test_dir, exist_ok=True)
            monitored_dirs = [test_dir]
            
        return monitored_dirs
    
    async def _scan_filesystem(self, directories: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Scansiona le directory specificate e raccoglie informazioni sui file.
        
        Args:
            directories: Lista di directory da scansionare
            
        Returns:
            Dizionario con percorsi file e relativi metadati
        """
        files_info = {}
        
        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"Directory non trovata: {directory}")
                continue
                
            logger.info(f"Scansione directory: {directory}")
            
            for root, _, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Verifica estensione supportata
                    _, ext = os.path.splitext(filename)
                    if ext.lower() not in self.supported_extensions:
                        continue
                        
                    try:
                        # Ottieni metadati file
                        stat = os.stat(file_path)
                        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        size = stat.st_size
                        
                        # Calcola hash del file
                        file_hash = await self._calculate_file_hash(file_path)
                        
                        files_info[file_path] = {
                            "path": file_path,
                            "modified_time": modified_time,
                            "size": size,
                            "hash": file_hash
                        }
                        
                    except Exception as e:
                        logger.warning(f"Errore scansione file {file_path}: {str(e)}")
        
        return files_info
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calcola l'hash MD5 di un file.
        
        Args:
            file_path: Percorso del file
            
        Returns:
            Hash MD5 del file
        """
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                
        return hash_md5.hexdigest()
    
    async def _reconcile_vectorstore(self, 
                                   job_id: int,
                                   files_info: Dict[str, Dict[str, Any]],
                                   collection_name: str,
                                   delete_missing: bool,
                                   batch_size: int) -> Tuple[int, int, int, int]:
        """
        Riconcilia il vectorstore con le informazioni del filesystem.
        
        Args:
            job_id: ID del job
            files_info: Dizionario con informazioni sui file
            collection_name: Nome della collezione ChromaDB
            delete_missing: Se eliminare i documenti presenti nel vectorstore ma non nel filesystem
            batch_size: Dimensione del batch per l'elaborazione
            
        Returns:
            Tuple con conteggio (aggiunti, aggiornati, rimossi, errori)
        """
        # Inizializza contatori
        added_count = 0
        updated_count = 0
        removed_count = 0
        error_count = 0
        processed_count = 0
        
        try:
            # Ottieni tutti i documenti dal vectorstore
            vectorstore_docs = await self._get_all_vectorstore_documents(collection_name)
            
            # Crea set di percorsi per confronto rapido
            filesystem_paths = set(files_info.keys())
            vectorstore_paths = {doc.get("metadata", {}).get("source_path") for doc in vectorstore_docs if doc.get("metadata")}
            
            # Rimuovi None dal set
            vectorstore_paths = {path for path in vectorstore_paths if path}
            
            # 1. Identifica file nel filesystem ma non nel vectorstore (da aggiungere)
            paths_to_add = filesystem_paths - vectorstore_paths
            
            # 2. Identifica file sia nel filesystem che nel vectorstore (da verificare per aggiornamenti)
            paths_to_check = filesystem_paths.intersection(vectorstore_paths)
            
            # 3. Identifica file nel vectorstore ma non nel filesystem (da rimuovere)
            paths_to_remove = vectorstore_paths - filesystem_paths
            
            logger.info(f"Riconciliazione: {len(paths_to_add)} da aggiungere, {len(paths_to_check)} da verificare, {len(paths_to_remove)} da rimuovere")
            
            # Processa file da aggiungere in batch
            for i in range(0, len(paths_to_add), batch_size):
                batch = list(paths_to_add)[i:i+batch_size]
                
                for file_path in batch:
                    try:
                        # Qui dovremmo inviare il file al servizio di elaborazione PDF
                        # che lo analizza, estrae testo, crea embeddings e lo aggiunge al vectorstore
                        # Per ora, simuliamo solo l'operazione di base
                        
                        # TODO: Implementare chiamata al servizio di elaborazione PDF
                        # Simuliamo solo il successo dell'operazione
                        added_count += 1
                        
                    except Exception as e:
                        logger.error(f"Errore aggiunta file {file_path}: {str(e)}")
                        error_count += 1
                
                processed_count += len(batch)
                
                # Aggiorna stato job
                await self.db.update_job(
                    job_id=job_id,
                    processed_files=processed_count,
                    added_files=added_count,
                    updated_files=updated_count,
                    removed_files=removed_count,
                    errors=error_count
                )
            
            # Processa file da verificare in batch
            for i in range(0, len(paths_to_check), batch_size):
                batch = list(paths_to_check)[i:i+batch_size]
                
                for file_path in batch:
                    try:
                        # Verifica se il file è stato modificato confrontando hash
                        file_info = files_info[file_path]
                        file_hash = file_info["hash"]
                        
                        # Trova documento nel vectorstore
                        doc = next((doc for doc in vectorstore_docs if doc.get("metadata", {}).get("source_path") == file_path), None)
                        
                        if doc and doc.get("metadata", {}).get("file_hash") != file_hash:
                            # File modificato, aggiorna
                            # Qui dovremmo inviare il file al servizio di elaborazione PDF
                            # Per ora, simuliamo solo l'operazione
                            
                            # TODO: Implementare chiamata al servizio di elaborazione PDF
                            # Simuliamo solo il successo dell'operazione
                            updated_count += 1
                            
                    except Exception as e:
                        logger.error(f"Errore verifica file {file_path}: {str(e)}")
                        error_count += 1
                
                processed_count += len(batch)
                
                # Aggiorna stato job
                await self.db.update_job(
                    job_id=job_id,
                    processed_files=processed_count,
                    added_files=added_count,
                    updated_files=updated_count,
                    removed_files=removed_count,
                    errors=error_count
                )
            
            # Processa file da rimuovere se richiesto
            if delete_missing:
                for i in range(0, len(paths_to_remove), batch_size):
                    batch = list(paths_to_remove)[i:i+batch_size]
                    
                    for file_path in batch:
                        try:
                            # Trova documento nel vectorstore
                            doc = next((doc for doc in vectorstore_docs if doc.get("metadata", {}).get("source_path") == file_path), None)
                            
                            if doc and doc.get("id"):
                                # Rimuovi documento dal vectorstore
                                # TODO: Implementare rimozione effettiva dal vectorstore
                                # Simuliamo solo il successo dell'operazione
                                removed_count += 1
                                
                        except Exception as e:
                            logger.error(f"Errore rimozione file {file_path}: {str(e)}")
                            error_count += 1
                    
                    processed_count += len(batch)
                    
                    # Aggiorna stato job
                    await self.db.update_job(
                        job_id=job_id,
                        processed_files=processed_count,
                        added_files=added_count,
                        updated_files=updated_count,
                        removed_files=removed_count,
                        errors=error_count
                    )
            
            return added_count, updated_count, removed_count, error_count
            
        except Exception as e:
            logger.error(f"Errore riconciliazione: {str(e)}")
            return added_count, updated_count, removed_count, error_count + 1
    
    async def _get_all_vectorstore_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Ottiene tutti i documenti dal vectorstore.
        
        Args:
            collection_name: Nome della collezione
            
        Returns:
            Lista di documenti dal vectorstore
        """
        # In una implementazione reale, dovremmo recuperare tutti i documenti dal vectorstore
        # Per ora, restituiamo una lista vuota
        
        # TODO: Implementare recupero effettivo dal vectorstore
        return []

# Singleton pattern per il servizio di riconciliazione
_reconciliation_service = None

def get_reconciliation_service() -> ReconciliationService:
    """
    Ottiene l'istanza singleton del servizio di riconciliazione.
    
    Returns:
        Istanza di ReconciliationService
    """
    global _reconciliation_service
    if _reconciliation_service is None:
        _reconciliation_service = ReconciliationService()
        
    return _reconciliation_service
