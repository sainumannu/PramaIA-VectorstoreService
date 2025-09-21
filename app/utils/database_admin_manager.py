""""""""""""

Database Admin Manager - Gestore per amministrazione e monitoraggio del database documenti.

Database Admin Manager - Gestore per amministrazione e monitoraggio del database documenti.

Estende DocumentManager con funzionalità specifiche per:

- Health check e diagnostica connessioniDatabaseAdminManager - Gestore per amministrazione e monitoraggio del databaseDatabaseAdminMaclass DatabaseAdminManager(BaseDocumentManager):

- Statistiche dettagliate e monitoraggio

- Operazioni di manutenzione e resetEstende DocumentManager con funzionalità specifiche per:

- API di gestione avanzate per interfacce admin

"""- Health check e diagnostica connessioni    """



import logging- Statistiche dettagliate e monitoraggio

import os

import shutil- Operazioni di manutenzione e resetEstende DocumentManager con funzionalità specifiche per:    Gestore per amministrazione e monitoraggio del database documenti.

from datetime import datetime

from typing import Dict, List, Any, Optional, Tuple- API di gestione avanzate per interfacce admin

from pathlib import Path

"""- Amministrazione sistema    

from app.utils.document_manager import DocumentManager as BaseDocumentManager



logger = logging.getLogger(__name__)

import logging- Monitoraggio statistiche      Estende DocumentManager con funzionalità specifiche per:

class DatabaseAdminManager(BaseDocumentManager):

    """import os

    Gestore per amministrazione e monitoraggio del database documenti.

    import shutil- Health check e diagnostica    - Health check e diagnostica connessioni

    Estende DocumentManager con funzionalità specifiche per:

    - Amministrazione sistemafrom datetime import datetime

    - Monitoraggio statistiche  

    - Health check e diagnosticafrom typing import Dict, List, Any, Optional, Tuple- Reset e manutenzione database    - Statistiche dettagliate e monitoraggio

    - Reset e manutenzione database

    """from pathlib import Path

    

    def __init__(self):"""    - Operazioni di manutenzione e reset

        """Inizializza DatabaseAdminManager ereditando da DocumentManager."""

        super().__init__()from app.utils.document_manager import DocumentManager as BaseDocumentManager

        logger.info("DatabaseAdminManager inizializzato")

        - API di gestione avanzate per interfacce admin

    def get_full_health_report(self) -> Dict[str, Any]:

        """logger = logging.getLogger(__name__)

        Genera un report completo dello stato di salute del sistema.

        from app.utils.document_manager import DocumentManager as BaseDocumentManager    """store per amministrazione e monitoraggio del database

        Returns:

            Dict completo con diagnostica dettagliata di entrambi i databaseclass DatabaseAdminManager(BaseDocumentManager):

        """

        try:    """import os

            report = {

                'timestamp': datetime.now().isoformat(),    Gestore per amministrazione e monitoraggio del database documenti.

                'overall_status': 'unknown',

                'sqlite_health': self._check_sqlite_health(),    import loggingEstende DocumentManager con funzionalità specifiche per:

                'chromadb_health': self._check_chromadb_health(),

                'sync_status': self._check_sync_status(),    Estende DocumentManager con funzionalità specifiche per:

                'performance_metrics': self._get_performance_metrics()

            }    - Amministrazione sistemaimport chromadb- Amministrazione sistema

            

            # Determina stato generale    - Monitoraggio statistiche

            sqlite_ok = report['sqlite_health']['status'] == 'healthy'

            chroma_ok = report['chromadb_health']['status'] == 'healthy'    - Health check e diagnosticafrom pathlib import Path- Monitoraggio statistiche  

            sync_ok = report['sync_status']['status'] == 'synchronized'

                - Reset e manutenzione database

            if sqlite_ok and chroma_ok and sync_ok:

                report['overall_status'] = 'healthy'    """from typing import Dict, Any, List, Optional- Health check e diagnostica

            elif sqlite_ok and chroma_ok:

                report['overall_status'] = 'warning'  # Database OK ma sync issues    

            else:

                report['overall_status'] = 'critical'    def __init__(self):- Reset e manutenzione database

                

            return report        """Inizializza DatabaseAdminManager ereditando da DocumentManager."""

            

        except Exception as e:        super().__init__()# Configurazione logger"""

            logger.error(f"Errore generazione health report: {e}")

            return {        logger.info("DatabaseAdminManager inizializzato")

                'timestamp': datetime.now().isoformat(),

                'overall_status': 'error',    logger = logging.getLogger(__name__)

                'error': str(e)

            }    def get_full_health_report(self) -> Dict[str, Any]:

    

    def _check_sqlite_health(self) -> Dict[str, Any]:        """from app.utils.document_manager import DocumentManager as BaseDocumentManager

        """Verifica stato di salute del database SQLite."""

        try:        Genera un report completo dello stato di salute del sistema.

            # Controlla connessione

            doc_count = self.metadata_db.get_document_count()        class DatabaseAdminManager(BaseDocumentManager):import os

            

            # Verifica integrità database        Returns:

            db_path = self.metadata_db.db_path

            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0            Dict completo con diagnostica dettagliata di entrambi i database    """import logging

            

            return {        """

                'status': 'healthy',

                'document_count': doc_count,        try:    Gestore per amministrazione e monitoraggio del database documenti.import chromadb

                'database_size_bytes': db_size,

                'database_path': db_path,            report = {

                'last_check': datetime.now().isoformat()

            }                'timestamp': datetime.now().isoformat(),    from pathlib import Path

            

        except Exception as e:                'overall_status': 'unknown',

            return {

                'status': 'error',                'sqlite_health': self._check_sqlite_health(),    Estende DocumentManager con funzionalità specifiche per:from typing import Dict, Any, List, Optional

                'error': str(e),

                'last_check': datetime.now().isoformat()                'chromadb_health': self._check_chromadb_health(),

            }

                    'sync_status': self._check_sync_status(),    - Health check e diagnostica connessioni

    def _check_chromadb_health(self) -> Dict[str, Any]:

        """Verifica stato di salute del database ChromaDB."""                'performance_metrics': self._get_performance_metrics()

        try:

            collections = self.vector_db.list_collections()            }    - Statistiche dettagliate e monitoraggio# Configurazione logger

            collection = self.vector_db.get_collection()

                        

            chroma_count = 0

            if collection:            # Determina stato generale    - Operazioni di manutenzione e resetlogger = logging.getLogger(__name__)

                try:

                    chroma_count = collection.count()            sqlite_ok = report['sqlite_health']['status'] == 'healthy'

                except Exception:

                    pass  # Count può fallire su collezioni vuote            chroma_ok = report['chromadb_health']['status'] == 'healthy'    - API di gestione avanzate per interfacce admin

            

            persist_dir = getattr(self.vector_db, '_persist_dir', 'unknown')            sync_ok = report['sync_status']['status'] == 'synchronized'

            

            return {                """class DatabaseAdminManager(BaseDocumentManager):

                'status': 'healthy',

                'collections': collections,            if sqlite_ok and chroma_ok and sync_ok:

                'document_count': chroma_count,

                'persist_directory': persist_dir,                report['overall_status'] = 'healthy'        """

                'last_check': datetime.now().isoformat()

            }            elif sqlite_ok and chroma_ok:

            

        except Exception as e:                report['overall_status'] = 'warning'  # Database OK ma sync issues    def __init__(self, data_dir: Optional[str] = None):    Gestore per amministrazione e monitoraggio del database ibrido.

            return {

                'status': 'error',            else:

                'error': str(e),

                'last_check': datetime.now().isoformat()                report['overall_status'] = 'critical'        """Inizializza il gestore esteso."""    

            }

                    

    def _check_sync_status(self) -> Dict[str, Any]:

        """Verifica la sincronizzazione tra SQLite e ChromaDB."""            return report        super().__init__(data_dir=data_dir)    Estende HybridDocumentManager con funzionalità specifiche per:

        try:

            sqlite_count = self.metadata_db.get_document_count()            

            

            # Conta documenti in ChromaDB        except Exception as e:        self.chroma_path = os.path.join(self.data_dir, "chroma_db")    - Health check e diagnostica connessioni

            chroma_count = 0

            collection = self.vector_db.get_collection()            logger.error(f"Errore generazione health report: {e}")

            if collection:

                try:            return {        - Statistiche dettagliate e monitoraggio

                    chroma_count = collection.count()

                except Exception:                'timestamp': datetime.now().isoformat(),

                    pass

                            'overall_status': 'error',    def check_connection(self) -> bool:    - Operazioni di manutenzione e reset

            sync_diff = abs(sqlite_count - chroma_count)

            sync_percentage = 100.0                'error': str(e)

            

            if sqlite_count > 0:            }        """    - API di gestione avanzate per interfacce admin

                sync_percentage = ((min(sqlite_count, chroma_count) / sqlite_count) * 100)

                

            status = 'synchronized'

            if sync_diff > 0:    def _check_sqlite_health(self) -> Dict[str, Any]:        Verifica se la connessione a ChromaDB è funzionante.    """

                if sync_percentage < 90:

                    status = 'out_of_sync'        """Verifica stato di salute del database SQLite."""

                else:

                    status = 'minor_drift'        try:            

            

            return {            # Controlla connessione

                'status': status,

                'sqlite_documents': sqlite_count,            doc_count = self.metadata_db.get_document_count()        Returns:    def __init__(self, data_dir: str = None):

                'chromadb_documents': chroma_count,

                'sync_difference': sync_diff,            

                'sync_percentage': round(sync_percentage, 2),

                'last_check': datetime.now().isoformat()            # Verifica integrità database            True se la connessione è ok, False altrimenti.        """Inizializza il gestore esteso."""

            }

                        db_path = self.metadata_db.db_path

        except Exception as e:

            return {            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0        """        super().__init__(data_dir=data_dir)

                'status': 'error',

                'error': str(e),            

                'last_check': datetime.now().isoformat()

            }            return {        try:        self.chroma_path = os.path.join(self.data_dir, "chroma_db")

    

    def _get_performance_metrics(self) -> Dict[str, Any]:                'status': 'healthy',

        """Raccoglie metriche di performance del sistema."""

        try:                'document_count': doc_count,            # Tenta di creare un client ChromaDB e verificare la connessione    

            return {

                'avg_query_time_ms': None,  # Da implementare con monitoring                'database_size_bytes': db_size,

                'last_operation_time': None,

                'cache_hit_rate': None,                'database_path': db_path,            from chromadb import PersistentClient    def check_connection(self) -> bool:

                'memory_usage_mb': None,

                'last_collected': datetime.now().isoformat()                'last_check': datetime.now().isoformat()

            }

        except Exception as e:            }            client = PersistentClient(path=self.chroma_path)        """

            return {

                'error': str(e),            

                'last_collected': datetime.now().isoformat()

            }        except Exception as e:            # Tenta di elencare le collezioni per verificare che il client funzioni        Verifica se la connessione a ChromaDB è funzionante.

    

    def perform_full_reset(self, confirm: bool = False) -> Dict[str, Any]:            return {

        """

        Esegue un reset completo di entrambi i database.                'status': 'error',            collections = client.list_collections()        

        

        Args:                'error': str(e),

            confirm: Conferma esplicita per operazione distruttiva

                            'last_check': datetime.now().isoformat()            return True        Returns:

        Returns:

            Dict con risultato dell'operazione            }

        """

        if not confirm:            except Exception as e:            True se la connessione è ok, False altrimenti.

            return {

                'success': False,    def _check_chromadb_health(self) -> Dict[str, Any]:

                'error': 'Reset richiede conferma esplicita (confirm=True)',

                'timestamp': datetime.now().isoformat()        """Verifica stato di salute del database ChromaDB."""            logger.error(f"Errore nella verifica della connessione a ChromaDB: {str(e)}")        """

            }

                try:

        try:

            logger.warning("Iniziando reset completo del database...")            collections = self.vector_db.list_collections()            return False        try:

            

            # 1. Reset SQLite            collection = self.vector_db.get_collection()

            sqlite_result = self._reset_sqlite_database()

                                        # Tenta di creare un client ChromaDB e verificare la connessione

            # 2. Reset ChromaDB

            chroma_result = self._reset_chromadb_database()            chroma_count = 0

            

            success = sqlite_result['success'] and chroma_result['success']            if collection:    def get_persistence_path(self) -> str:            from chromadb import PersistentClient

            

            result = {                try:

                'success': success,

                'sqlite_reset': sqlite_result,                    chroma_count = collection.count()        """            client = PersistentClient(path=self.chroma_path)

                'chromadb_reset': chroma_result,

                'timestamp': datetime.now().isoformat()                except Exception:

            }

                                pass  # Count può fallire su collezioni vuote        Ottiene il percorso della directory di persistenza di ChromaDB.            # Tenta di elencare le collezioni per verificare che il client funzioni

            if success:

                logger.info("Reset completo completato con successo")            

            else:

                logger.error("Reset completo parzialmente fallito")            persist_dir = getattr(self.vector_db, '_persist_dir', 'unknown')                    collections = client.list_collections()

                

            return result            

            

        except Exception as e:            return {        Returns:            return True

            logger.error(f"Errore durante reset completo: {e}")

            return {                'status': 'healthy',

                'success': False,

                'error': str(e),                'collections': collections,            Path della directory di persistenza.        except Exception as e:

                'timestamp': datetime.now().isoformat()

            }                'document_count': chroma_count,

                'persist_directory': persist_dir,        """            logger.error(f"Errore nella verifica della connessione a ChromaDB: {str(e)}")

                'last_check': datetime.now().isoformat()

            }        return self.chroma_path            return False

            

        except Exception as e:        

            return {

                'status': 'error',    def get_document_count(self) -> int:    def get_statistics(self) -> Dict[str, Any]:

                'error': str(e),

                'last_check': datetime.now().isoformat()        """        """

            }

            Ottiene il numero totale di documenti nel vector store.        Ottiene statistiche dettagliate sul vector store.

    def _check_sync_status(self) -> Dict[str, Any]:

        """Verifica la sincronizzazione tra SQLite e ChromaDB."""                

        try:

            sqlite_count = self.metadata_db.get_document_count()        Returns:        Returns:

            

            # Conta documenti in ChromaDB            Numero di documenti.            Dizionario con le statistiche.

            chroma_count = 0

            collection = self.vector_db.get_collection()        """        """

            if collection:

                try:        try:        try:

                    chroma_count = collection.count()

                except Exception:            from chromadb import PersistentClient            # Carica le statistiche di base

                    pass

                        client = PersistentClient(path=self.chroma_path)            stats = self._load_stats()

            sync_diff = abs(sqlite_count - chroma_count)

            sync_percentage = 100.0            collections = client.list_collections()            

            

            if sqlite_count > 0:                        # Aggiungi statistiche aggiuntive

                sync_percentage = ((min(sqlite_count, chroma_count) / sqlite_count) * 100)

                        total = 0            # Conta documenti nel ChromaDB

            status = 'synchronized'

            if sync_diff > 0:            for collection in collections:            try:

                if sync_percentage < 90:

                    status = 'out_of_sync'                total += collection.count()                from chromadb import PersistentClient

                else:

                    status = 'minor_drift'                            client = PersistentClient(path=self.chroma_path)

            

            return {            return total                collections = client.list_collections()

                'status': status,

                'sqlite_documents': sqlite_count,        except Exception as e:                

                'chromadb_documents': chroma_count,

                'sync_difference': sync_diff,            logger.error(f"Errore nel conteggio dei documenti: {str(e)}")                total_documents = 0

                'sync_percentage': round(sync_percentage, 2),

                'last_check': datetime.now().isoformat()            return 0                collection_names = []

            }

                                

        except Exception as e:

            return {    def list_documents(self, limit: int = 20, offset: int = 0, metadata_only: bool = False) -> List[Dict[str, Any]]:                for collection in collections:

                'status': 'error',

                'error': str(e),        """                    collection_size = collection.count()

                'last_check': datetime.now().isoformat()

            }        Ottiene l'elenco dei documenti nel vector store.                    total_documents += collection_size

    

    def _get_performance_metrics(self) -> Dict[str, Any]:                            collection_names.append({

        """Raccoglie metriche di performance del sistema."""

        try:        Args:                        "name": collection.name,

            return {

                'avg_query_time_ms': None,  # Da implementare con monitoring            limit: Numero massimo di documenti da restituire.                        "count": collection_size

                'last_operation_time': None,

                'cache_hit_rate': None,            offset: Offset per la paginazione.                    })

                'memory_usage_mb': None,

                'last_collected': datetime.now().isoformat()            metadata_only: Se True, restituisce solo i metadati senza il contenuto.                

            }

        except Exception as e:                            stats["total_documents"] = total_documents

            return {

                'error': str(e),        Returns:                stats["collections"] = collection_names

                'last_collected': datetime.now().isoformat()

            }            Lista di documenti.                

    

    def perform_full_reset(self, confirm: bool = False) -> Dict[str, Any]:        """                # Calcola dimensione media dei chunk

        """

        Esegue un reset completo di entrambi i database.        try:                if total_documents > 0:

        

        Args:            from chromadb import PersistentClient                    # Questo è solo una stima approssimativa

            confirm: Conferma esplicita per operazione distruttiva

                        client = PersistentClient(path=self.chroma_path)                    avg_chunk_size = 1.5  # Kb, valore medio stimato

        Returns:

            Dict con risultato dell'operazione            collections = client.list_collections()                    stats["avg_chunk_size"] = avg_chunk_size

        """

        if not confirm:                            

            return {

                'success': False,            all_documents = []                # Modello di embedding utilizzato

                'error': 'Reset richiede conferma esplicita (confirm=True)',

                'timestamp': datetime.now().isoformat()                            stats["embedding_model"] = "sentence-transformers/all-MiniLM-L6-v2"

            }

                    for collection in collections:                

        try:

            logger.warning("Iniziando reset completo del database...")                try:            except Exception as chroma_error:

            

            # 1. Reset SQLite                    # Ottieni tutti i documenti dalla collezione                logger.warning(f"Errore nel recupero delle statistiche ChromaDB: {str(chroma_error)}")

            sqlite_result = self._reset_sqlite_database()

                                result = collection.get(                stats["chroma_error"] = str(chroma_error)

            # 2. Reset ChromaDB

            chroma_result = self._reset_chromadb_database()                        limit=limit + offset            

            

            success = sqlite_result['success'] and chroma_result['success']                    )            return stats

            

            result = {                            except Exception as e:

                'success': success,

                'sqlite_reset': sqlite_result,                    # Crea una lista di documenti            logger.error(f"Errore nel recupero delle statistiche: {str(e)}")

                'chromadb_reset': chroma_result,

                'timestamp': datetime.now().isoformat()                    documents = []            return {

            }

                                if result and "metadatas" in result and "documents" in result and "ids" in result:                "error": str(e),

            if success:

                logger.info("Reset completo completato con successo")                        for i in range(len(result["ids"])):                "total_documents": 0,

            else:

                logger.error("Reset completo parzialmente fallito")                            doc = {                "collections": []

                

            return result                                "id": result["ids"][i],            }

            

        except Exception as e:                                "metadata": result["metadatas"][i]    

            logger.error(f"Errore durante reset completo: {e}")

            return {                            }    def get_persistence_path(self) -> str:

                'success': False,

                'error': str(e),                            if not metadata_only:        """

                'timestamp': datetime.now().isoformat()

            }                                doc["content"] = result["documents"][i] if i < len(result["documents"]) else ""        Ottiene il percorso della directory di persistenza di ChromaDB.

    

    def _reset_sqlite_database(self) -> Dict[str, Any]:                            documents.append(doc)        

        """Reset del database SQLite."""

        try:                            Returns:

            # Chiudi connessioni esistenti

            if hasattr(self.metadata_db, '_connection') and self.metadata_db._connection:                    all_documents.extend(documents)            Path della directory di persistenza.

                self.metadata_db._connection.close()

                            except Exception as coll_error:        """

            # Rimuovi file database

            db_path = self.metadata_db.db_path                    logger.warning(f"Errore nel recupero dei documenti dalla collezione {collection.name}: {str(coll_error)}")        return self.chroma_path

            if os.path.exists(db_path):

                os.remove(db_path)                

                logger.info(f"Database SQLite rimosso: {db_path}")

                        # Applica limit e offset    def get_document_count(self) -> int:

            # Ricrea database

            self.metadata_db._init_database()            return all_documents[offset:offset + limit]        """

            

            return {        except Exception as e:        Ottiene il numero totale di documenti nel vector store.

                'success': True,

                'message': 'Database SQLite resettato e ricreato',            logger.error(f"Errore nel recupero dei documenti: {str(e)}")        

                'database_path': db_path

            }            return []        Returns:

            

        except Exception as e:                Numero di documenti.

            logger.error(f"Errore reset SQLite: {e}")

            return {    def reset(self) -> bool:        """

                'success': False,

                'error': str(e)        """        try:

            }

            Resetta il vector store eliminando tutti i documenti.            from chromadb import PersistentClient

    def _reset_chromadb_database(self) -> Dict[str, Any]:

        """Reset del database ChromaDB."""                    client = PersistentClient(path=self.chroma_path)

        try:

            # Rimuovi directory di persistenza        Returns:            collections = client.list_collections()

            persist_dir = getattr(self.vector_db, '_persist_dir', None)

            if persist_dir and os.path.exists(persist_dir):            True se il reset è avvenuto con successo, False altrimenti.            

                shutil.rmtree(persist_dir)

                logger.info(f"Directory ChromaDB rimossa: {persist_dir}")        """            total = 0

            

            # Reinizializza client        try:            for collection in collections:

            self.vector_db._client = None

            self.vector_db._collection = None            from chromadb import PersistentClient                total += collection.count()

            self.vector_db._init_client()

                                    

            return {

                'success': True,            # Prima elimina tutte le collezioni esistenti            return total

                'message': 'Database ChromaDB resettato e ricreato',

                'persist_directory': persist_dir            try:        except Exception as e:

            }

                            client = PersistentClient(path=self.chroma_path)            logger.error(f"Errore nel conteggio dei documenti: {str(e)}")

        except Exception as e:

            logger.error(f"Errore reset ChromaDB: {e}")                collections = client.list_collections()            return 0

            return {

                'success': False,                    

                'error': str(e)

            }                for collection in collections:    def list_documents(self, limit: int = 20, offset: int = 0, metadata_only: bool = False) -> List[Dict[str, Any]]:

    

    def repair_sync_issues(self) -> Dict[str, Any]:                    client.delete_collection(collection.name)        """

        """

        Tenta di riparare problemi di sincronizzazione tra i database.                        Ottiene l'elenco dei documenti nel vector store.

        

        Returns:                logger.info(f"Tutte le collezioni ChromaDB eliminate con successo")        

            Dict con risultato dell'operazione di riparazione

        """            except Exception as del_error:        Args:

        try:

            logger.info("Iniziando riparazione sincronizzazione database...")                logger.error(f"Errore nell'eliminazione delle collezioni ChromaDB: {str(del_error)}")            limit: Numero massimo di documenti da restituire.

            

            # Ottieni documenti da entrambi i database                        offset: Offset per la paginazione.

            sqlite_docs = self.metadata_db.get_documents()

                        # Poi, a seconda della gravità del problema, potrebbe essere necessario eliminare fisicamente la directory            metadata_only: Se True, restituisce solo i metadati senza il contenuto.

            collection = self.vector_db.get_collection()

            chroma_docs = []            import shutil            

            if collection:

                try:            try:        Returns:

                    # Ottieni tutti i documenti da ChromaDB

                    chroma_data = collection.get()                if os.path.exists(self.chroma_path):            Lista di documenti.

                    chroma_docs = chroma_data.get('ids', [])

                except Exception as e:                    # Rimuovi la directory ChromaDB        """

                    logger.warning(f"Errore lettura documenti ChromaDB: {e}")

                                shutil.rmtree(self.chroma_path)        try:

            # Trova documenti mancanti

            sqlite_ids = {doc['id'] for doc in sqlite_docs}                    logger.info(f"Directory ChromaDB eliminata: {self.chroma_path}")            from chromadb import PersistentClient

            chroma_ids = set(chroma_docs)

                                            client = PersistentClient(path=self.chroma_path)

            missing_in_chroma = sqlite_ids - chroma_ids

            missing_in_sqlite = chroma_ids - sqlite_ids                    # Ricrea la directory vuota            collections = client.list_collections()

            

            repair_results = {                    os.makedirs(self.chroma_path, exist_ok=True)            

                'missing_in_chromadb': len(missing_in_chroma),

                'missing_in_sqlite': len(missing_in_sqlite),            except Exception as rm_error:            all_documents = []

                'repaired_chromadb': 0,

                'repaired_sqlite': 0,                logger.error(f"Errore nella rimozione della directory ChromaDB: {str(rm_error)}")            

                'errors': []

            }                return False            for collection in collections:

            

            # Ripara documenti mancanti in ChromaDB                            try:

            for doc_id in missing_in_chroma:

                try:            return True                    # Ottieni tutti i documenti dalla collezione

                    doc = next((d for d in sqlite_docs if d['id'] == doc_id), None)

                    if doc and collection:        except Exception as e:                    result = collection.get(

                        collection.add(

                            documents=[doc.get('content', '')],            logger.error(f"Errore nel reset del vector store: {str(e)}")                        limit=limit + offset

                            metadatas=[{k: v for k, v in doc.items() if k != 'content'}],

                            ids=[doc_id]            return False                    )

                        )

                        repair_results['repaired_chromadb'] += 1                    

                except Exception as e:

                    repair_results['errors'].append(f"Errore riparazione {doc_id} in ChromaDB: {e}")# Alias per compatibilità con i vecchi nomi                    # Crea una lista di documenti

            

            # Per documenti mancanti in SQLite, li rimuoviamo da ChromaDB ExtendedMetadataStoreManager = DatabaseAdminManager                    documents = []

            # (assumiamo SQLite come fonte di verità)

            for doc_id in missing_in_sqlite:ExtendedHybridDocumentManager = DatabaseAdminManager                    if result and "metadatas" in result and "documents" in result and "ids" in result:

                try:                        for i in range(len(result["ids"])):

                    if collection:                            doc = {

                        collection.delete(ids=[doc_id])                                "id": result["ids"][i],

                        repair_results['repaired_sqlite'] += 1                                "metadata": result["metadatas"][i]

                except Exception as e:                            }

                    repair_results['errors'].append(f"Errore rimozione {doc_id} da ChromaDB: {e}")                            if not metadata_only:

                                            doc["content"] = result["documents"][i] if i < len(result["documents"]) else ""

            success = len(repair_results['errors']) == 0                            documents.append(doc)

                                

            result = {                    all_documents.extend(documents)

                'success': success,                except Exception as coll_error:

                'repair_summary': repair_results,                    logger.warning(f"Errore nel recupero dei documenti dalla collezione {collection.name}: {str(coll_error)}")

                'timestamp': datetime.now().isoformat()            

            }            # Applica limit e offset

                        return all_documents[offset:offset + limit]

            logger.info(f"Riparazione completata. Successo: {success}")        except Exception as e:

            return result            logger.error(f"Errore nel recupero dei documenti: {str(e)}")

                        return []

        except Exception as e:    

            logger.error(f"Errore durante riparazione sync: {e}")    def reset(self) -> bool:

            return {        """

                'success': False,        Resetta il vector store eliminando tutti i documenti.

                'error': str(e),        

                'timestamp': datetime.now().isoformat()        Returns:

            }            True se il reset è avvenuto con successo, False altrimenti.

            """

    def get_detailed_statistics(self) -> Dict[str, Any]:        try:

        """            from chromadb import PersistentClient

        Restituisce statistiche dettagliate del sistema.            

                    # Prima elimina tutte le collezioni esistenti

        Returns:            try:

            Dict con statistiche complete di entrambi i database                client = PersistentClient(path=self.chroma_path)

        """                collections = client.list_collections()

        try:                

            # Statistiche base ereditate                for collection in collections:

            base_stats = self.get_statistics()                    client.delete_collection(collection.name)

                            

            # Statistiche aggiuntive per admin                logger.info(f"Tutte le collezioni ChromaDB eliminate con successo")

            admin_stats = {            except Exception as del_error:

                'system_info': {                logger.error(f"Errore nell'eliminazione delle collezioni ChromaDB: {str(del_error)}")

                    'python_version': None,  # Da implementare            

                    'chromadb_version': None,            # Poi, a seconda della gravità del problema, potrebbe essere necessario eliminare fisicamente la directory

                    'sqlite_version': None,            import shutil

                    'disk_usage': self._get_disk_usage(),            try:

                },                if os.path.exists(self.chroma_path):

                'performance_history': {                    # Rimuovi la directory ChromaDB

                    'last_24h_operations': None,  # Da implementare con logging                    shutil.rmtree(self.chroma_path)

                    'avg_response_time': None,                    logger.info(f"Directory ChromaDB eliminata: {self.chroma_path}")

                    'error_rate': None                    

                },                    # Ricrea la directory vuota

                'maintenance_info': {                    os.makedirs(self.chroma_path, exist_ok=True)

                    'last_backup': None,            except Exception as rm_error:

                    'last_optimization': None,                logger.error(f"Errore nella rimozione della directory ChromaDB: {str(rm_error)}")

                    'next_scheduled_maintenance': None                return False

                }            

            }            # Resetta le statistiche

                        stats = self._load_stats()

            # Combina statistiche            stats["documents_total"] = 0

            return {            stats["documents_today"] = 0

                **base_stats,            stats["documents_in_queue"] = 0

                'admin_statistics': admin_stats,            stats["collections"] = 0

                'generated_at': datetime.now().isoformat()            self._save_stats(stats)

            }            

                        return True

        except Exception as e:        except Exception as e:

            logger.error(f"Errore generazione statistiche dettagliate: {e}")            logger.error(f"Errore nel reset del vector store: {str(e)}")

            return {            return False

                'error': str(e),

                'generated_at': datetime.now().isoformat()# Alias per compatibilità con i vecchi nomi

            }ExtendedMetadataStoreManager = DatabaseAdminManager

    ExtendedHybridDocumentManager = DatabaseAdminManager

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Calcola l'utilizzo del disco per i database."""
        try:
            usage = {}
            
            # SQLite
            if hasattr(self.metadata_db, 'db_path'):
                sqlite_path = self.metadata_db.db_path
                if os.path.exists(sqlite_path):
                    usage['sqlite_size_bytes'] = os.path.getsize(sqlite_path)
            
            # ChromaDB
            persist_dir = getattr(self.vector_db, '_persist_dir', None)
            if persist_dir and os.path.exists(persist_dir):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(persist_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                usage['chromadb_size_bytes'] = total_size
            
            return usage
            
        except Exception as e:
            logger.error(f"Errore calcolo disk usage: {e}")
            return {'error': str(e)}