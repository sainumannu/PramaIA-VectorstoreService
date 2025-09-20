"""
Vectorstore Manager - Utility per la gestione del vectorstore.
Versione migliorata con utilizzo di database SQLite.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.utils.document_database import DocumentDatabase

# Configurazione logger
logger = logging.getLogger(__name__)

class VectorstoreManager:
    """
    Gestore centralizzato per il vectorstore.
    Versione aggiornata che utilizza un database SQLite invece di file JSON.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Inizializza il gestore del vectorstore.
        
        Args:
            data_dir: Directory per la memorizzazione dei dati. Default alla directory 'data' nella directory corrente.
        """
        self.data_dir = data_dir or os.path.join(os.getcwd(), "data")
        self.stats_file = os.path.join(self.data_dir, "stats.json")
        
        # Assicurarsi che le directory esistano
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inizializzare il database
        self.document_db = DocumentDatabase(data_dir=self.data_dir)
        
        # Inizializzare i file rimanenti
        self._init_files()
        
        # Ricalcola le statistiche dopo l'inizializzazione
        self.recalculate_stats()
    
    def _init_files(self):
        """
        Inizializza i file di dati se non esistono.
        """
        if not os.path.exists(self.stats_file):
            stats = {
                "documents_total": 0,
                "documents_today": 0,
                "documents_in_queue": 0,
                "collections": 0,
                "processing_queue": 0,
                "last_update": datetime.now().isoformat(),
                "daily_stats": []
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def _load_stats(self) -> Dict[str, Any]:
        """
        Carica le statistiche dal file.
        
        Returns:
            Dizionario con le statistiche.
        """
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Errore nel caricamento delle statistiche: {str(e)}")
            return {
                "documents_total": 0,
                "documents_today": 0,
                "documents_in_queue": 0,
                "collections": 0,
                "processing_queue": 0,
                "last_update": datetime.now().isoformat(),
                "daily_stats": []
            }
    
    def _save_stats(self, stats: Dict[str, Any]) -> bool:
        """
        Salva le statistiche nel file.
        
        Args:
            stats: Dizionario con le statistiche da salvare.
            
        Returns:
            True se il salvataggio è avvenuto con successo, False altrimenti.
        """
        try:
            stats["last_update"] = datetime.now().isoformat()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio delle statistiche: {str(e)}")
            return False
    
    def recalculate_stats(self) -> bool:
        """
        Ricalcola le statistiche in base ai documenti effettivamente presenti.
        Aggiorna il conteggio totale e delle collezioni.
        
        Returns:
            True se l'operazione è avvenuta con successo, False altrimenti.
        """
        try:
            stats = self._load_stats()
            
            # Aggiorna il conteggio totale di documenti
            stats["documents_total"] = self.document_db.get_document_count()
            
            # Aggiorna il conteggio delle collezioni
            collections = self.document_db.get_collections()
            stats["collections"] = len(collections)
            
            # Calcola i documenti aggiunti oggi
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = 0
            
            # Aggiorna le statistiche giornaliere
            daily_stats = stats.get("daily_stats", [])
            
            # Trova le statistiche del giorno corrente o crea un nuovo record
            today_stats = None
            for day_stats in daily_stats:
                if day_stats.get("date") == today:
                    today_stats = day_stats
                    today_count = day_stats.get("processed", 0)
                    break
            
            stats["documents_today"] = today_count
            
            return self._save_stats(stats)
        except Exception as e:
            logger.error(f"Errore nella ricalcolazione delle statistiche: {str(e)}")
            return False
    
    def get_documents(self, collection: Optional[str] = None, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Ottiene tutti i documenti, opzionalmente filtrati per collezione.
        
        Args:
            collection: Nome della collezione per filtrare i risultati (opzionale)
            limit: Numero massimo di documenti da restituire
            offset: Offset per la paginazione
        
        Returns:
            Lista di documenti con i relativi metadati.
        """
        return self.document_db.get_documents(collection=collection, limit=limit, offset=offset)
    
    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Aggiunge un documento.
        
        Args:
            document: Documento da aggiungere.
            
        Returns:
            True se l'aggiunta è avvenuta con successo, False altrimenti.
        """
        success = self.document_db.add_document(document)
        
        if success:
            self._update_stats_add_document(document)
        
        return success
    
    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento.
        
        Args:
            document_id: ID del documento da eliminare.
            
        Returns:
            True se l'eliminazione è avvenuta con successo, False altrimenti.
        """
        success = self.document_db.delete_document(document_id)
        
        if success:
            self._update_stats_delete_document()
        
        return success
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene un documento specifico.
        
        Args:
            document_id: ID del documento da ottenere.
            
        Returns:
            Il documento se trovato, None altrimenti.
        """
        return self.document_db.get_document(document_id)
    
    def get_collections(self) -> List[str]:
        """
        Ottiene tutte le collezioni presenti nei documenti.
        
        Returns:
            Lista di nomi di collezioni.
        """
        return self.document_db.get_collections()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Ottiene le statistiche.
        
        Returns:
            Dizionario con le statistiche.
        """
        return self._load_stats()
    
    def _update_stats_add_document(self, document: Dict[str, Any], is_update: bool = False) -> None:
        """
        Aggiorna le statistiche dopo l'aggiunta di un documento.
        
        Args:
            document: Documento aggiunto.
            is_update: Se True, il documento è un aggiornamento e non un nuovo documento.
        """
        stats = self._load_stats()
        
        if not is_update:
            stats["documents_total"] = stats.get("documents_total", 0) + 1
            
            # Aggiorna le statistiche del giorno
            today = datetime.now().strftime("%Y-%m-%d")
            stats["documents_today"] = stats.get("documents_today", 0) + 1
            
            # Aggiorna le statistiche giornaliere
            daily_stats = stats.get("daily_stats", [])
            
            # Trova le statistiche del giorno corrente o crea un nuovo record
            today_stats = None
            for day_stats in daily_stats:
                if day_stats.get("date") == today:
                    today_stats = day_stats
                    break
            
            if not today_stats:
                today_stats = {"date": today, "processed": 0, "indexed": 0}
                daily_stats.append(today_stats)
            
            today_stats["processed"] = today_stats.get("processed", 0) + 1
            today_stats["indexed"] = today_stats.get("indexed", 0) + 1
            
            stats["daily_stats"] = daily_stats
        
        # Aggiorna il conteggio delle collezioni
        collections = self.get_collections()
        stats["collections"] = len(collections)
        
        self._save_stats(stats)
    
    def _update_stats_delete_document(self) -> None:
        """
        Aggiorna le statistiche dopo l'eliminazione di un documento.
        """
        stats = self._load_stats()
        
        stats["documents_total"] = max(0, stats.get("documents_total", 0) - 1)
        
        # Aggiorna il conteggio delle collezioni
        collections = self.get_collections()
        stats["collections"] = len(collections)
        
        self._save_stats(stats)
    
    def search_documents(self, 
                         query: str, 
                         collection: Optional[str] = None,
                         metadata_filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca sui documenti in base al testo e ai metadati.
        
        Args:
            query: Testo da cercare nel nome del file
            collection: Nome della collezione (opzionale)
            metadata_filters: Filtri sui metadati (opzionale)
            limit: Numero massimo di documenti da restituire
            offset: Offset per la paginazione
            
        Returns:
            Lista di documenti che corrispondono ai criteri di ricerca.
        """
        return self.document_db.search_documents(
            query=query,
            collection=collection,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset
        )
    
    def get_collection_stats(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ottiene statistiche su una collezione o su tutte le collezioni.
        
        Args:
            collection_name: Nome della collezione (opzionale, se None vengono restituite statistiche globali)
            
        Returns:
            Dizionario con statistiche sulla collezione.
        """
        return self.document_db.get_collection_stats(collection_name=collection_name)
    
    def export_all_to_json(self, output_file: Optional[str] = None) -> bool:
        """
        Esporta tutti i documenti in un file JSON.
        Utile per backup o compatibilità con versioni precedenti.
        
        Args:
            output_file: Percorso del file di output (opzionale)
            
        Returns:
            True se l'esportazione è avvenuta con successo, False altrimenti.
        """
        return self.document_db.export_to_json(output_file=output_file)
    
    def vacuum_database(self) -> bool:
        """
        Esegue un'operazione VACUUM sul database per ottimizzare lo spazio.
        Utile dopo molte operazioni di eliminazione.
        
        Returns:
            True se l'operazione è avvenuta con successo, False altrimenti.
        """
        return self.document_db.vacuum_database()
