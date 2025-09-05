"""
Modulo per la gestione del database SQLite del servizio.
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.utils.config import get_settings

# Configurazione logging
logger = logging.getLogger(__name__)

class Database:
    """Classe per la gestione del database SQLite."""
    
    def __init__(self, db_path: str = None):
        """
        Inizializza il database.
        
        Args:
            db_path: Percorso del database. Se None, usa il valore dalle impostazioni.
        """
        if db_path is None:
            db_path = get_settings().db_path
            
        self.db_path = db_path
        self.conn = None
    
    async def initialize(self) -> bool:
        """
        Inizializza il database.
        
        Returns:
            True se l'inizializzazione ha successo, False altrimenti.
        """
        try:
            # Crea directory del database se non esiste
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            
            # Apri connessione
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            # Crea tabelle
            await self._create_tables()
            
            logger.info(f"Database inizializzato: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore inizializzazione database: {str(e)}")
            return False
    
    async def _create_tables(self):
        """Crea le tabelle del database."""
        cursor = self.conn.cursor()
        
        # Tabella dei job di riconciliazione
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reconciliation_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            total_files INTEGER,
            processed_files INTEGER,
            added_files INTEGER,
            updated_files INTEGER,
            removed_files INTEGER,
            errors INTEGER,
            delete_missing BOOLEAN NOT NULL,
            batch_size INTEGER NOT NULL,
            error_message TEXT
        )
        ''')
        
        # Tabella delle impostazioni
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Tabella delle statistiche
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Inserisci impostazioni predefinite se non esistono
        settings = [
            ("schedule_enabled", str(get_settings().schedule_enabled).lower(), datetime.now().isoformat()),
            ("schedule_time", get_settings().schedule_time, datetime.now().isoformat()),
            ("batch_size", str(get_settings().default_batch_size), datetime.now().isoformat()),
            ("delete_missing", "true", datetime.now().isoformat())
        ]
        
        cursor.executemany('''
        INSERT OR IGNORE INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ''', settings)
        
        self.conn.commit()
    
    async def create_job(self, delete_missing: bool, batch_size: int) -> int:
        """
        Crea un nuovo job di riconciliazione.
        
        Args:
            delete_missing: Se eliminare documenti mancanti
            batch_size: Dimensione del batch
            
        Returns:
            ID del job creato
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT INTO reconciliation_jobs 
            (status, start_time, delete_missing, batch_size, processed_files, added_files, updated_files, removed_files, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "running", 
                datetime.now().isoformat(), 
                delete_missing, 
                batch_size,
                0, 0, 0, 0, 0  # Inizializza contatori a 0
            ))
            
            self.conn.commit()
            job_id = cursor.lastrowid
            
            logger.info(f"Creato job di riconciliazione {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Errore creazione job: {str(e)}")
            raise
    
    async def update_job(self, 
                        job_id: int, 
                        status: str = None,
                        end_time: str = None,
                        total_files: int = None,
                        processed_files: int = None,
                        added_files: int = None,
                        updated_files: int = None,
                        removed_files: int = None,
                        errors: int = None,
                        error_message: str = None) -> bool:
        """
        Aggiorna lo stato di un job.
        
        Args:
            job_id: ID del job
            status: Nuovo stato del job
            end_time: Orario di fine
            total_files: Totale file elaborati
            processed_files: Numero di file processati
            added_files: Numero di file aggiunti
            updated_files: Numero di file aggiornati
            removed_files: Numero di file rimossi
            errors: Numero di errori
            error_message: Messaggio di errore
            
        Returns:
            True se l'aggiornamento ha successo, False altrimenti
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            # Costruisci query dinamica in base ai parametri forniti
            update_parts = []
            params = []
            
            if status is not None:
                update_parts.append("status = ?")
                params.append(status)
                
            if end_time is not None:
                update_parts.append("end_time = ?")
                params.append(end_time)
                
            if total_files is not None:
                update_parts.append("total_files = ?")
                params.append(total_files)
                
            if processed_files is not None:
                update_parts.append("processed_files = ?")
                params.append(processed_files)
                
            if added_files is not None:
                update_parts.append("added_files = ?")
                params.append(added_files)
                
            if updated_files is not None:
                update_parts.append("updated_files = ?")
                params.append(updated_files)
                
            if removed_files is not None:
                update_parts.append("removed_files = ?")
                params.append(removed_files)
                
            if errors is not None:
                update_parts.append("errors = ?")
                params.append(errors)
                
            if error_message is not None:
                update_parts.append("error_message = ?")
                params.append(error_message)
            
            # Se non ci sono aggiornamenti, esci
            if not update_parts:
                return False
                
            # Aggiungi ID job ai parametri
            params.append(job_id)
            
            # Esegui query
            cursor.execute(f'''
            UPDATE reconciliation_jobs SET {", ".join(update_parts)} WHERE id = ?
            ''', params)
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Aggiornato job {job_id}: {', '.join(update_parts)}")
                return True
            else:
                logger.warning(f"Job {job_id} non trovato per aggiornamento")
                return False
                
        except Exception as e:
            logger.error(f"Errore aggiornamento job {job_id}: {str(e)}")
            return False
    
    async def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Ottiene i dettagli di un job.
        
        Args:
            job_id: ID del job
            
        Returns:
            Dettagli del job o None se non trovato
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT * FROM reconciliation_jobs WHERE id = ?
            ''', (job_id,))
            
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Errore recupero job {job_id}: {str(e)}")
            return None
    
    async def get_all_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Ottiene tutti i job, ordinati per ID decrescente.
        
        Args:
            limit: Numero massimo di job da restituire
            offset: Offset per paginazione
            
        Returns:
            Lista di job
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT * FROM reconciliation_jobs ORDER BY id DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Errore recupero jobs: {str(e)}")
            return []
    
    async def get_running_jobs(self) -> List[Dict[str, Any]]:
        """
        Ottiene tutti i job in esecuzione.
        
        Returns:
            Lista di job in esecuzione
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT * FROM reconciliation_jobs WHERE status = 'running' ORDER BY id DESC
            ''')
            
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Errore recupero jobs in esecuzione: {str(e)}")
            return []
    
    async def get_setting(self, key: str) -> Optional[str]:
        """
        Ottiene il valore di un'impostazione.
        
        Args:
            key: Chiave dell'impostazione
            
        Returns:
            Valore dell'impostazione o None se non trovata
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT value FROM settings WHERE key = ?
            ''', (key,))
            
            row = cursor.fetchone()
            
            if row:
                return row["value"]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Errore recupero impostazione {key}: {str(e)}")
            return None
    
    async def set_setting(self, key: str, value: str) -> bool:
        """
        Imposta il valore di un'impostazione.
        
        Args:
            key: Chiave dell'impostazione
            value: Valore dell'impostazione
            
        Returns:
            True se l'operazione ha successo, False altrimenti
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            
            self.conn.commit()
            
            logger.info(f"Impostazione {key} = {value}")
            return True
                
        except Exception as e:
            logger.error(f"Errore impostazione {key}: {str(e)}")
            return False
    
    async def get_all_settings(self) -> Dict[str, str]:
        """
        Ottiene tutte le impostazioni.
        
        Returns:
            Dizionario delle impostazioni
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT key, value FROM settings
            ''')
            
            rows = cursor.fetchall()
            
            return {row["key"]: row["value"] for row in rows}
                
        except Exception as e:
            logger.error(f"Errore recupero impostazioni: {str(e)}")
            return {}
    
    async def update_stats(self, key: str, value: str) -> bool:
        """
        Aggiorna una statistica.
        
        Args:
            key: Chiave della statistica
            value: Valore della statistica
            
        Returns:
            True se l'operazione ha successo, False altrimenti
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO stats (key, value, updated_at)
            VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            
            self.conn.commit()
            
            return True
                
        except Exception as e:
            logger.error(f"Errore aggiornamento statistica {key}: {str(e)}")
            return False
    
    async def get_all_stats(self) -> Dict[str, str]:
        """
        Ottiene tutte le statistiche.
        
        Returns:
            Dizionario delle statistiche
        """
        try:
            if self.conn is None:
                await self.initialize()
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT key, value FROM stats
            ''')
            
            rows = cursor.fetchall()
            
            return {row["key"]: row["value"] for row in rows}
                
        except Exception as e:
            logger.error(f"Errore recupero statistiche: {str(e)}")
            return {}
    
    def close(self):
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()
            self.conn = None

# Singleton pattern per il database
_db_instance = None

def get_db() -> Database:
    """
    Ottiene l'istanza singleton del database.
    
    Returns:
        Istanza di Database
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        
    return _db_instance

async def init_db() -> bool:
    """
    Inizializza il database.
    
    Returns:
        True se l'inizializzazione ha successo, False altrimenti
    """
    db = get_db()
    return await db.initialize()
