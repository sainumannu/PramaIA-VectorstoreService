"""
Modulo per la gestione dello scheduler dei job di riconciliazione.
"""

import logging
import asyncio
import schedule
import time
import threading
from datetime import datetime

from app.core.reconciliation import get_reconciliation_service
from app.db.database import get_db
from app.utils.config import get_settings

# Configurazione logging
logger = logging.getLogger(__name__)

class ReconciliationScheduler:
    """Scheduler per i job di riconciliazione."""
    
    def __init__(self):
        """Inizializza lo scheduler."""
        self.scheduler_thread = None
        self.stop_event = None
        self.running = False
    
    def start(self):
        """Avvia lo scheduler in un thread separato."""
        if self.running:
            logger.warning("Scheduler già in esecuzione")
            return
        
        self.stop_event = threading.Event()
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            daemon=True
        )
        self.scheduler_thread.start()
        self.running = True
        
        logger.info("Scheduler avviato")
    
    def stop(self):
        """Ferma lo scheduler."""
        if not self.running:
            return
            
        if self.stop_event:
            self.stop_event.set()
            
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        self.running = False
        schedule.clear()
        
        logger.info("Scheduler fermato")
    
    def _run_scheduler(self):
        """Funzione principale dello scheduler."""
        try:
            # Configura i job schedulati
            self._configure_schedules()
            
            logger.info("Thread scheduler avviato")
            
            # Loop principale dello scheduler
            while not self.stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Errore nello scheduler: {str(e)}")
            self.running = False
    
    def _configure_schedules(self):
        """Configura i job schedulati in base alle impostazioni."""
        # Pulisci eventuali job esistenti
        schedule.clear()
        
        # Ottieni impostazioni di pianificazione
        enabled = get_settings().schedule_enabled
        schedule_time = get_settings().schedule_time
        
        if not enabled:
            logger.info("Pianificazione disabilitata")
            return
        
        # Pianifica il job di riconciliazione
        logger.info(f"Configurazione job riconciliazione pianificato alle {schedule_time}")
        
        # Schedula il job
        schedule.every().day.at(schedule_time).do(self._run_reconciliation_job)
        
        logger.info(f"Job riconciliazione pianificato alle {schedule_time}")
    
    def _run_reconciliation_job(self):
        """Esegue un job di riconciliazione pianificato."""
        logger.info("Avvio job riconciliazione pianificato")
        
        # Crea una nuova event loop per operazioni asincrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Ottieni servizio di riconciliazione
            reconciliation_service = get_reconciliation_service()
            
            # Ottieni impostazioni di riconciliazione dal database
            db = get_db()
            settings = loop.run_until_complete(db.get_all_settings())
            
            delete_missing = settings.get("delete_missing", "true").lower() == "true"
            batch_size = int(settings.get("batch_size", "1000"))
            
            # Avvia job di riconciliazione
            job_id = loop.run_until_complete(
                reconciliation_service.start_reconciliation(
                    delete_missing=delete_missing,
                    batch_size=batch_size
                )
            )
            
            logger.info(f"Job riconciliazione pianificato avviato con ID {job_id}")
            
        except Exception as e:
            logger.error(f"Errore avvio job riconciliazione pianificato: {str(e)}")
            
        finally:
            loop.close()
            
        return True  # Importante: restituisci True per mantenere il job pianificato

# Singleton pattern per lo scheduler
_scheduler_instance = None

def get_scheduler() -> ReconciliationScheduler:
    """
    Ottiene l'istanza singleton dello scheduler.
    
    Returns:
        Istanza di ReconciliationScheduler
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ReconciliationScheduler()
        
    return _scheduler_instance

def start_scheduler():
    """Avvia lo scheduler."""
    scheduler = get_scheduler()
    scheduler.start()

def stop_scheduler():
    """Ferma lo scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()
