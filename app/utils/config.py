"""
Modulo di configurazione che utilizza Pydantic per la gestione delle impostazioni.
"""

import os
from functools import lru_cache
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Impostazioni dell'applicazione."""
    
    # Impostazioni generali
    app_name: str = "VectorstoreService"
    log_level: str = Field(default="INFO")
    
    # Impostazioni del database
    db_path: str = Field(default="./vectorstore.db")
    
    # Impostazioni del vectorstore
    vectorstore_path: str = Field(default="./chroma_db")
    default_collection_name: str = Field(default="default")
    default_namespace: str = Field(default="default")
    default_embedding_model: str = Field(default="openai")
    
    # Impostazioni di pianificazione
    schedule_enabled: bool = Field(default=True)
    schedule_time: str = Field(default="03:00")  # HH:MM in formato 24 ore
    
    # Impostazioni di riconciliazione
    default_batch_size: int = Field(default=1000)
    
    # Impostazioni API OpenAI (per embedding)
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    
    # Impostazioni server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8090)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Restituisce le impostazioni dell'applicazione.
    
    La funzione è decorata con @lru_cache per evitare di leggere le impostazioni
    ogni volta che viene chiamata.
    """
    return Settings()
