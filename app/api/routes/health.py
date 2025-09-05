from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import time

from app.core.chroma_manager import ChromaManager
from app.db.database import Database
from app.api.models import (
    HealthResponse,
    ErrorResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)

@router.get(
    "",
    response_model=HealthResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def health_check(
    chroma_manager: ChromaManager = Depends(),
    database: Database = Depends()
):
    """
    Check the health of the service and its dependencies.
    """
    logger.info("Running health check")
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": start_time,
        "uptime": 0,  # Will be populated by the service
        "dependencies": {}
    }
    
    # Check ChromaDB connection
    try:
        chroma_health = chroma_manager.health_check()
        health_status["dependencies"]["chroma"] = {
            "status": "healthy",
            "details": chroma_health
        }
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["dependencies"]["chroma"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check database connection
    try:
        db_health = database.health_check()
        health_status["dependencies"]["database"] = {
            "status": "healthy",
            "details": db_health
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Add response time
    health_status["response_time_ms"] = int((time.time() - start_time) * 1000)
    
    return HealthResponse(**health_status)

@router.get(
    "/ready",
    response_model=Dict[str, str],
    responses={
        503: {"model": ErrorResponse, "description": "Service Unavailable"}
    }
)
async def readiness_check(
    chroma_manager: ChromaManager = Depends(),
    database: Database = Depends()
):
    """
    Check if the service is ready to accept requests.
    """
    logger.info("Running readiness check")
    
    try:
        # Check if ChromaDB is ready
        chroma_manager.health_check()
        
        # Check if database is ready
        database.health_check()
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )

@router.get(
    "/live",
    response_model=Dict[str, str]
)
async def liveness_check():
    """
    Check if the service is alive.
    """
    logger.info("Running liveness check")
    return {"status": "alive"}
