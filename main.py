"""
PramaIA-VectorstoreService - Servizio centralizzato per la gestione del vectorstore.

Questo servizio fornisce:
1. API REST completa per operazioni CRUD sul vectorstore
2. Riconciliazione pianificata tra filesystem e vectorstore
3. Gestione delle collezioni e dei namespace
4. Operazioni di embedding e recupero documenti
"""

import os
import sys
import logging
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configurazione logging
from app.utils.logger import setup_logging
from app.utils.config import get_settings

# Importa router API
from app.api import api_router

# Importa database e scheduler
from app.db.database import init_db, get_db
from app.scheduler.scheduler import start_scheduler, stop_scheduler

# Carica variabili d'ambiente
load_dotenv()

# Configura logger
logger = setup_logging()

# Crea applicazione FastAPI
app = FastAPI(
    title="PramaIA VectorstoreService",
    description="Servizio centralizzato per la gestione del vectorstore e la riconciliazione con il filesystem",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, limitare agli origini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra il router API centralizzato
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Operazioni da eseguire all'avvio dell'applicazione."""
    try:
        logger.info("Inizializzazione VectorstoreService...")
        
        # Inizializza database
        await init_db()
        logger.info("Database inizializzato.")
        
        # Avvia scheduler
        if get_settings().schedule_enabled:
            start_scheduler()
            logger.info(f"Scheduler avviato con pianificazione: {get_settings().schedule_time}")
        else:
            logger.info("Scheduler disabilitato da configurazione.")
        
        logger.info(f"VectorstoreService avviato con successo. Versione: 1.0.0")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione: {str(e)}")
        # In un ambiente di produzione, potremmo voler terminare il processo
        # sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Operazioni da eseguire alla chiusura dell'applicazione."""
    try:
        logger.info("Arresto VectorstoreService...")
        
        # Arresta scheduler
        stop_scheduler()
        logger.info("Scheduler arrestato.")
        
        logger.info("VectorstoreService arrestato con successo.")
    except Exception as e:
        logger.error(f"Errore durante l'arresto: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8090"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Avvia server Uvicorn
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
