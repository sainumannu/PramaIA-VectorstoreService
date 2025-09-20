"""
Vectorstore Manager - Utility per la gestione del vectorstore.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configurazione logger
logger = logging.getLogger(__name__)

class VectorstoreManager:
    def recalculate_stats(self) -> bool:
        """
        Ricalcola le statistiche in base ai documenti effettivamente presenti.
        Aggiorna il conteggio totale e delle collezioni.
        """
        documents = self._load_documents()
        stats = self._load_stats()
        stats["documents_total"] = len(documents)
        collections = set()
        for doc in documents:
            collection = doc.get("collection")
            if collection:
                collections.add(collection)
        stats["collections"] = len(collections)
        return self._save_stats(stats)
    """
    Gestore centralizzato per il vectorstore.
    Gestisce la memorizzazione dei documenti e le relative operazioni.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Inizializza il gestore del vectorstore.
        
        Args:
            data_dir: Directory per la memorizzazione dei dati. Default alla directory 'data' nella directory corrente.
        """
        self.data_dir = data_dir or os.path.join(os.getcwd(), "data")
        self.documents_file = os.path.join(self.data_dir, "documents.json")
        self.stats_file = os.path.join(self.data_dir, "stats.json")
        
        # Assicurarsi che le directory esistano
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inizializzare i file se non esistono
        self._init_files()
    
    def _init_files(self):
        """
        Inizializza i file di dati se non esistono.
        """
        if not os.path.exists(self.documents_file):
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump({"documents": []}, f, ensure_ascii=False, indent=2)
        
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
    
    def _load_documents(self) -> List[Dict[str, Any]]:
        """
        Carica i documenti dal file.
        
        Returns:
            Lista di documenti.
        """
        try:
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("documents", [])
        except Exception as e:
            logger.error(f"Errore nel caricamento dei documenti: {str(e)}")
            return []
    
    def _save_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Salva i documenti nel file.
        
        Args:
            documents: Lista di documenti da salvare.
            
        Returns:
            True se il salvataggio è avvenuto con successo, False altrimenti.
        """
        try:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump({"documents": documents}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio dei documenti: {str(e)}")
            return False
    
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
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Ottiene tutti i documenti.
        
        Returns:
            Lista di documenti.
        """
        return self._load_documents()
    
    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Aggiunge un documento.
        
        Args:
            document: Documento da aggiungere.
            
        Returns:
            True se l'aggiunta è avvenuta con successo, False altrimenti.
        """
        documents = self._load_documents()
        
        # Verifica se il documento esiste già
        for i, doc in enumerate(documents):
            if doc.get("id") == document.get("id"):
                # Aggiorna il documento esistente
                documents[i] = document
                self._update_stats_add_document(document, is_update=True)
                return self._save_documents(documents)
        
        # Aggiungi il nuovo documento
        documents.append(document)
        self._update_stats_add_document(document)
        return self._save_documents(documents)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento.
        
        Args:
            document_id: ID del documento da eliminare.
            
        Returns:
            True se l'eliminazione è avvenuta con successo, False altrimenti.
        """
        documents = self._load_documents()
        
        # Trova e rimuovi il documento
        for i, doc in enumerate(documents):
            if doc.get("id") == document_id:
                del documents[i]
                self._update_stats_delete_document()
                return self._save_documents(documents)
        
        # Documento non trovato
        return False
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene un documento specifico.
        
        Args:
            document_id: ID del documento da ottenere.
            
        Returns:
            Il documento se trovato, None altrimenti.
        """
        documents = self._load_documents()
        
        # Trova il documento
        for doc in documents:
            if doc.get("id") == document_id:
                return doc
        
        # Documento non trovato
        return None
    
    def get_collections(self) -> List[str]:
        """
        Ottiene tutte le collezioni presenti nei documenti.
        
        Returns:
            Lista di nomi di collezioni.
        """
        documents = self._load_documents()
        
        # Estrai le collezioni
        collections = set()
        for doc in documents:
            collection = doc.get("collection")
            if collection:
                collections.add(collection)
        
        return list(collections)
    
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
        collections = set(self.get_collections())
        stats["collections"] = len(collections)
        
        self._save_stats(stats)
    
    def _update_stats_delete_document(self) -> None:
        """
        Aggiorna le statistiche dopo l'eliminazione di un documento.
        """
        stats = self._load_stats()
        
        stats["documents_total"] = max(0, stats.get("documents_total", 0) - 1)
        
        # Aggiorna il conteggio delle collezioni
        collections = set(self.get_collections())
        stats["collections"] = len(collections)
        
        self._save_stats(stats)
