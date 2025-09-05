from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional

from app.core.reconciliation import ReconciliationManager
from app.api.models import (
    ReconciliationRequest,
    ReconciliationResponse,
    ReconciliationStatusResponse,
    ReconciliationListResponse,
    ErrorResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])
logger = get_logger(__name__)

@router.post(
    "",
    response_model=ReconciliationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def start_reconciliation(
    request: ReconciliationRequest,
    background_tasks: BackgroundTasks,
    reconciliation_manager: ReconciliationManager = Depends()
):
    """
    Start a reconciliation job between filesystem and vectorstore.
    """
    logger.info(f"Starting reconciliation for collection: {request.collection_name}")
    try:
        job_id = reconciliation_manager.start_reconciliation(
            collection_name=request.collection_name,
            file_paths=request.file_paths,
            scan_dir=request.scan_dir,
            delete_missing=request.delete_missing,
            background_tasks=background_tasks
        )
        
        return ReconciliationResponse(
            job_id=job_id,
            status="started",
            message=f"Reconciliation job started for collection: {request.collection_name}"
        )
    except ValueError as e:
        logger.error(f"Invalid reconciliation request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reconciliation request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error starting reconciliation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start reconciliation: {str(e)}"
        )

@router.get(
    "/{job_id}",
    response_model=ReconciliationStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_reconciliation_status(
    job_id: str,
    reconciliation_manager: ReconciliationManager = Depends()
):
    """
    Get the status of a reconciliation job.
    """
    logger.info(f"Getting status for reconciliation job: {job_id}")
    try:
        status_info = reconciliation_manager.get_reconciliation_status(job_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reconciliation job not found: {job_id}"
            )
        
        return ReconciliationStatusResponse(
            job_id=job_id,
            status=status_info.get("status", "unknown"),
            progress=status_info.get("progress", 0),
            total_files=status_info.get("total_files", 0),
            processed_files=status_info.get("processed_files", 0),
            added_files=status_info.get("added_files", 0),
            updated_files=status_info.get("updated_files", 0),
            deleted_files=status_info.get("deleted_files", 0),
            errors=status_info.get("errors", 0),
            error_details=status_info.get("error_details", []),
            start_time=status_info.get("start_time"),
            end_time=status_info.get("end_time")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting reconciliation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reconciliation status: {str(e)}"
        )

@router.get(
    "",
    response_model=ReconciliationListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def list_reconciliation_jobs(
    collection_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    reconciliation_manager: ReconciliationManager = Depends()
):
    """
    List all reconciliation jobs with optional filtering.
    """
    logger.info("Listing reconciliation jobs")
    try:
        jobs = reconciliation_manager.list_reconciliation_jobs(
            collection_name=collection_name,
            status=status,
            limit=limit,
            offset=offset
        )
        
        job_responses = []
        for job in jobs:
            job_responses.append(
                ReconciliationStatusResponse(
                    job_id=job.get("job_id"),
                    status=job.get("status", "unknown"),
                    progress=job.get("progress", 0),
                    total_files=job.get("total_files", 0),
                    processed_files=job.get("processed_files", 0),
                    added_files=job.get("added_files", 0),
                    updated_files=job.get("updated_files", 0),
                    deleted_files=job.get("deleted_files", 0),
                    errors=job.get("errors", 0),
                    error_details=job.get("error_details", []),
                    start_time=job.get("start_time"),
                    end_time=job.get("end_time"),
                    collection_name=job.get("collection_name")
                )
            )
        
        return ReconciliationListResponse(jobs=job_responses)
    except Exception as e:
        logger.error(f"Unexpected error listing reconciliation jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reconciliation jobs: {str(e)}"
        )

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def cancel_reconciliation_job(
    job_id: str,
    reconciliation_manager: ReconciliationManager = Depends()
):
    """
    Cancel a running reconciliation job.
    """
    logger.info(f"Cancelling reconciliation job: {job_id}")
    try:
        success = reconciliation_manager.cancel_reconciliation_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reconciliation job not found or already completed: {job_id}"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error cancelling reconciliation job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel reconciliation job: {str(e)}"
        )
