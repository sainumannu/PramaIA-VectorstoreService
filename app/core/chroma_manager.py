"""
Modulo principale per l'interazione con ChromaDB.
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.models.Collection import Collection

from app.utils.config import get_settings

# Configurazione logging
logger = logging.getLogger(__name__)

class ChromaManager:
    """
    Classe per la gestione delle operazioni su ChromaDB.
    Implementa tutte le operazioni CRUD e di ricerca necessarie.
    """
    
    def __init__(self):
        """Inizializza il manager ChromaDB."""
        self.client = None
        self.persist_directory = None
        self.initialized = False
    
    def initialize(self, persist_directory: str = None) -> bool:
        """
        Inizializza il client ChromaDB.
        
        Args:
            persist_directory: Directory di persistenza. Se None, usa il valore dalle impostazioni.
        
        Returns:
            True se l'inizializzazione ha successo, False altrimenti.
        
        Raises:
            RuntimeError: Se ChromaDB non può essere inizializzato.
        """
        if self.initialized and self.client:
            return True
            
        if persist_directory is None:
            persist_directory = get_settings().vectorstore_path
        
        try:
            # Crea directory se non esiste
            os.makedirs(persist_directory, exist_ok=True)
            
            # Inizializza client persistente
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.persist_directory = persist_directory
            self.initialized = True
            
            logger.info(f"Client ChromaDB inizializzato: {persist_directory}")
            return True
            
        except Exception as e:
            self.initialized = False
            error_msg = f"Errore inizializzazione ChromaDB: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_collection(self, collection_name: str, create_if_missing: bool = True) -> Collection:
        """
        Ottiene una collezione ChromaDB.
        
        Args:
            collection_name: Nome della collezione
            create_if_missing: Se True, crea la collezione se non esiste
        
        Returns:
            Collezione ChromaDB
        
        Raises:
            RuntimeError: Se la collezione non può essere ottenuta o creata.
        """
        if not self.initialized:
            self.initialize()
        
        try:
            try:
                # Prova a ottenere collezione esistente
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=None  # Usiamo embeddings pre-calcolati
                )
                logger.debug(f"Collezione esistente trovata: {collection_name}")
                
            except Exception as e:
                if not create_if_missing:
                    raise RuntimeError(f"Collezione {collection_name} non trovata: {str(e)}")
                
                # Crea nuova collezione
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": "cosine",  # Default
                        "description": f"Collection {collection_name} created by VectorstoreService",
                        "created_at": datetime.now().isoformat()
                    },
                    embedding_function=None
                )
                logger.info(f"Nuova collezione creata: {collection_name}")
            
            return collection
            
        except Exception as e:
            error_msg = f"Errore operazione su collezione {collection_name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        Lista tutte le collezioni disponibili.
        
        Returns:
            Lista di collezioni con metadati
        
        Raises:
            RuntimeError: Se le collezioni non possono essere elencate.
        """
        if not self.initialized:
            self.initialize()
        
        try:
            collections = self.client.list_collections()
            
            # Arricchisci con metadati
            result = []
            for collection in collections:
                coll_obj = self.client.get_collection(collection.name)
                
                # Ottieni conteggio documenti
                count = coll_obj.count()
                
                result.append({
                    "name": collection.name,
                    "id": collection.id,
                    "metadata": collection.metadata,
                    "document_count": count
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Errore elenco collezioni: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def add_documents(self, 
                     collection_name: str,
                     documents: List[str],
                     embeddings: List[List[float]],
                     metadatas: List[Dict[str, Any]] = None,
                     ids: List[str] = None,
                     namespace: str = None) -> List[str]:
        """
        Aggiunge documenti a una collezione.
        
        Args:
            collection_name: Nome della collezione
            documents: Lista di documenti (testo)
            embeddings: Lista di embeddings per i documenti
            metadatas: Lista di metadati per i documenti
            ids: Lista di ID per i documenti (se None, vengono generati)
            namespace: Namespace da utilizzare
        
        Returns:
            Lista di ID dei documenti aggiunti
        
        Raises:
            ValueError: Se ci sono parametri non validi
            RuntimeError: Se i documenti non possono essere aggiunti
        """
        if not documents or not embeddings:
            raise ValueError("Documenti ed embeddings richiesti")
            
        if len(documents) != len(embeddings):
            raise ValueError(f"Mismatch: {len(documents)} documenti vs {len(embeddings)} embeddings")
            
        if metadatas and len(documents) != len(metadatas):
            raise ValueError(f"Mismatch: {len(documents)} documenti vs {len(metadatas)} metadati")
        
        if not self.initialized:
            self.initialize()
        
        try:
            # Ottieni o crea la collezione
            collection = self.get_collection(collection_name)
            
            # Genera ID se non forniti
            if ids is None:
                ids = self._generate_document_ids(documents)
            elif len(ids) != len(documents):
                raise ValueError(f"Mismatch: {len(documents)} documenti vs {len(ids)} IDs")
            
            # Crea metadati default se non forniti
            if metadatas is None:
                metadatas = [{
                    "created_at": datetime.now().isoformat(),
                    "source": "vectorstore_service",
                } for _ in documents]
            
            # Assicura che ogni metadato abbia un timestamp
            for metadata in metadatas:
                if "created_at" not in metadata:
                    metadata["created_at"] = datetime.now().isoformat()
                
                # Converti eventuali valori non serializzabili in stringhe
                for key, value in list(metadata.items()):
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        metadata[key] = str(value)
            
            # Aggiungi documenti in batch per migliori performance
            batch_size = 100
            saved_ids = []
            
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                
                batch_ids = ids[i:end_idx]
                batch_documents = documents[i:end_idx]
                batch_embeddings = embeddings[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                # Parametri di collection.add
                add_params = {
                    "ids": batch_ids,
                    "embeddings": batch_embeddings,
                    "documents": batch_documents,
                    "metadatas": batch_metadatas
                }
                
                # Aggiungi namespace se specificato
                if namespace:
                    add_params["namespace"] = namespace
                
                # Aggiungi batch alla collezione
                collection.add(**add_params)
                
                saved_ids.extend(batch_ids)
                logger.debug(f"Salvato batch {i//batch_size + 1}: {len(batch_ids)} documenti")
            
            # Verifica risultato
            logger.info(f"Aggiunti {len(saved_ids)} documenti alla collezione {collection_name}")
            
            return saved_ids
            
        except Exception as e:
            error_msg = f"Errore aggiunta documenti: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_document(self, 
                   collection_name: str, 
                   document_id: str,
                   namespace: str = None) -> Optional[Dict[str, Any]]:
        """
        Ottiene un documento dalla collezione per ID.
        
        Args:
            collection_name: Nome della collezione
            document_id: ID del documento
            namespace: Namespace da utilizzare
        
        Returns:
            Documento se trovato, None altrimenti
        
        Raises:
            RuntimeError: Se ci sono errori nell'ottenimento del documento
        """
        if not self.initialized:
            self.initialize()
        
        try:
            collection = self.get_collection(collection_name, create_if_missing=False)
            
            # Parametri di query
            get_params = {
                "ids": [document_id],
                "include": ["documents", "metadatas", "embeddings"]
            }
            
            # Aggiungi namespace se specificato
            if namespace:
                get_params["namespace"] = namespace
            
            # Esegui query per ID
            result = collection.get(**get_params)
            
            # Verifica se il documento è stato trovato
            if not result["ids"] or not result["documents"]:
                logger.info(f"Documento {document_id} non trovato")
                return None
            
            # Costruisci oggetto documento
            document = {
                "id": result["ids"][0],
                "content": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
                "embedding": result["embeddings"][0] if result["embeddings"] else []
            }
            
            return document
            
        except Exception as e:
            # Se la collezione non esiste, restituisci None
            if "Collection not found" in str(e):
                logger.info(f"Collezione {collection_name} non trovata")
                return None
                
            error_msg = f"Errore recupero documento {document_id}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def update_document(self,
                      collection_name: str,
                      document_id: str,
                      document: str = None,
                      embedding: List[float] = None,
                      metadata: Dict[str, Any] = None,
                      namespace: str = None) -> bool:
        """
        Aggiorna un documento esistente.
        
        Args:
            collection_name: Nome della collezione
            document_id: ID del documento
            document: Nuovo contenuto del documento (se None, non viene aggiornato)
            embedding: Nuovo embedding (se None, non viene aggiornato)
            metadata: Nuovi metadati (se None, non viene aggiornato)
            namespace: Namespace da utilizzare
        
        Returns:
            True se l'aggiornamento ha successo, False se il documento non esiste
        
        Raises:
            RuntimeError: Se ci sono errori nell'aggiornamento
        """
        if not self.initialized:
            self.initialize()
            
        if document is None and embedding is None and metadata is None:
            raise ValueError("Almeno uno tra document, embedding o metadata deve essere specificato")
        
        try:
            # Verifica se il documento esiste
            existing = self.get_document(
                collection_name=collection_name, 
                document_id=document_id,
                namespace=namespace
            )
            
            if not existing:
                logger.warning(f"Documento {document_id} non trovato per l'aggiornamento")
                return False
            
            collection = self.get_collection(collection_name)
            
            # Prepara parametri di aggiornamento
            update_params = {
                "ids": [document_id]
            }
            
            # Aggiungi solo i parametri che sono stati specificati
            if document:
                update_params["documents"] = [document]
                
            if embedding:
                update_params["embeddings"] = [embedding]
                
            if metadata:
                # Unisci metadati esistenti con nuovi
                updated_metadata = existing["metadata"].copy() if existing["metadata"] else {}
                updated_metadata.update(metadata)
                
                # Aggiungi timestamp di aggiornamento
                updated_metadata["updated_at"] = datetime.now().isoformat()
                
                # Converti eventuali valori non serializzabili in stringhe
                for key, value in list(updated_metadata.items()):
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        updated_metadata[key] = str(value)
                
                update_params["metadatas"] = [updated_metadata]
            
            # Aggiungi namespace se specificato
            if namespace:
                update_params["namespace"] = namespace
            
            # Esegui aggiornamento
            collection.update(**update_params)
            
            logger.info(f"Documento {document_id} aggiornato con successo")
            return True
            
        except Exception as e:
            error_msg = f"Errore aggiornamento documento {document_id}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def delete_document(self, 
                      collection_name: str, 
                      document_id: str,
                      namespace: str = None) -> bool:
        """
        Elimina un documento dalla collezione.
        
        Args:
            collection_name: Nome della collezione
            document_id: ID del documento
            namespace: Namespace da utilizzare
        
        Returns:
            True se l'eliminazione ha successo, False se il documento non esiste
        
        Raises:
            RuntimeError: Se ci sono errori nell'eliminazione
        """
        if not self.initialized:
            self.initialize()
        
        try:
            # Verifica se la collezione esiste
            try:
                collection = self.get_collection(collection_name, create_if_missing=False)
            except Exception:
                logger.info(f"Collezione {collection_name} non trovata")
                return False
            
            # Parametri di eliminazione
            delete_params = {
                "ids": [document_id]
            }
            
            # Aggiungi namespace se specificato
            if namespace:
                delete_params["namespace"] = namespace
            
            # Esegui eliminazione
            collection.delete(**delete_params)
            
            logger.info(f"Documento {document_id} eliminato con successo")
            return True
            
        except Exception as e:
            error_msg = f"Errore eliminazione documento {document_id}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Elimina un'intera collezione.
        
        Args:
            collection_name: Nome della collezione
            
        Returns:
            True se l'eliminazione ha successo, False se la collezione non esiste
            
        Raises:
            RuntimeError: Se ci sono errori nell'eliminazione
        """
        if not self.initialized:
            self.initialize()
        
        try:
            # Verifica se la collezione esiste
            try:
                self.get_collection(collection_name, create_if_missing=False)
            except Exception:
                logger.info(f"Collezione {collection_name} non trovata")
                return False
                
            # Elimina collezione
            self.client.delete_collection(name=collection_name)
            
            logger.info(f"Collezione {collection_name} eliminata con successo")
            return True
            
        except Exception as e:
            error_msg = f"Errore eliminazione collezione {collection_name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def query_documents(self,
                       collection_name: str,
                       query_embedding: List[float],
                       top_k: int = 5,
                       namespace: str = None,
                       filter_metadata: Dict[str, Any] = None,
                       include_embeddings: bool = False,
                       similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        Esegue una query per similarità.
        
        Args:
            collection_name: Nome della collezione
            query_embedding: Embedding della query
            top_k: Numero massimo di risultati
            namespace: Namespace da utilizzare
            filter_metadata: Filtro sui metadati
            include_embeddings: Se includere gli embeddings nei risultati
            similarity_threshold: Soglia minima di similarità
            
        Returns:
            Lista di documenti con punteggio di similarità
            
        Raises:
            RuntimeError: Se ci sono errori nell'esecuzione della query
        """
        if not self.initialized:
            self.initialize()
        
        try:
            # Verifica se la collezione esiste
            try:
                collection = self.get_collection(collection_name, create_if_missing=False)
            except Exception:
                logger.info(f"Collezione {collection_name} non trovata")
                return []
            
            # Parametri di query
            include = ["documents", "metadatas", "distances"]
            if include_embeddings:
                include.append("embeddings")
                
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": include
            }
            
            # Aggiungi namespace se specificato
            if namespace:
                query_params["namespace"] = namespace
                
            # Aggiungi filtro se specificato
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            # Esegui query
            results = collection.query(**query_params)
            
            # Processa risultati
            documents_results = []
            
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]  # Prima query
                distances = results["distances"][0] if "distances" in results else []
                metadatas = results["metadatas"][0] if "metadatas" in results else []
                ids = results["ids"][0] if "ids" in results else []
                embeddings_results = results["embeddings"][0] if include_embeddings and "embeddings" in results else []
                
                for i, doc in enumerate(documents):
                    # Calcola similarity score (1 - distance per cosine)
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity_score = 1.0 - distance
                    
                    # Applica soglia di similarità
                    if similarity_threshold and similarity_score < similarity_threshold:
                        continue
                    
                    result = {
                        "id": ids[i] if i < len(ids) else f"unknown_{i}",
                        "content": doc,
                        "similarity_score": round(similarity_score, 4),
                        "distance": round(distance, 4)
                    }
                    
                    # Aggiungi metadati se disponibili
                    if i < len(metadatas):
                        result["metadata"] = metadatas[i]
                        
                    # Aggiungi embedding se richiesto
                    if include_embeddings and i < len(embeddings_results):
                        result["embedding"] = embeddings_results[i]
                    
                    documents_results.append(result)
            
            logger.info(f"Query su {collection_name}: trovati {len(documents_results)} documenti")
            return documents_results
            
        except Exception as e:
            error_msg = f"Errore query su {collection_name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _generate_document_ids(self, documents: List[str]) -> List[str]:
        """
        Genera ID univoci per i documenti.
        
        Args:
            documents: Lista di documenti
            
        Returns:
            Lista di ID univoci
        """
        document_ids = []
        timestamp = datetime.now().strftime('%Y%m%d')
        
        for i, doc in enumerate(documents):
            # Genera hash dal contenuto del documento per ID consistente
            content_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
            doc_id = f"doc_{timestamp}_{content_hash[:8]}_{i:04d}"
            document_ids.append(doc_id)
            
        return document_ids

# Singleton pattern per il ChromaManager
_chroma_manager = None

def get_chroma_manager() -> ChromaManager:
    """
    Ottiene l'istanza singleton del ChromaManager.
    
    Returns:
        Istanza di ChromaManager
    """
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
        
    return _chroma_manager
