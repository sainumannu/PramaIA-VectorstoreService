"""
Moduli comuni per le API.
"""

from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

# Common Models
class ErrorResponse(BaseModel):
    detail: str

# Collection Models
class CollectionCreateRequest(BaseModel):
    name: str = Field(..., description="The name of the collection")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the collection")

class CollectionResponse(BaseModel):
    id: str = Field(..., description="The unique ID of the collection")
    name: str = Field(..., description="The name of the collection")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata associated with the collection")

class CollectionListResponse(BaseModel):
    collections: List[CollectionResponse] = Field(..., description="List of collections")

# Document Models
class DocumentResponse(BaseModel):
    id: str = Field(..., description="The unique ID of the document")
    document: Optional[str] = Field(None, description="The document text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata associated with the document")
    distance: Optional[float] = Field(None, description="Distance score for query results")

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse] = Field(..., description="List of documents")

class DocumentAddRequest(BaseModel):
    documents: List[str] = Field(..., description="List of document contents to add")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="List of metadata dictionaries")
    ids: Optional[List[str]] = Field(None, description="List of document IDs")
    embeddings: Optional[List[List[float]]] = Field(None, description="List of pre-computed embeddings")
    
    @validator('metadatas')
    def validate_metadatas_length(cls, v, values):
        if v is not None and 'documents' in values and len(v) != len(values['documents']):
            raise ValueError("Length of metadatas must match length of documents")
        return v
    
    @validator('ids')
    def validate_ids_length(cls, v, values):
        if v is not None and 'documents' in values and len(v) != len(values['documents']):
            raise ValueError("Length of ids must match length of documents")
        return v
    
    @validator('embeddings')
    def validate_embeddings_length(cls, v, values):
        if v is not None and 'documents' in values and len(v) != len(values['documents']):
            raise ValueError("Length of embeddings must match length of documents")
        return v

    @validator('ids', pre=True)
    def generate_ids_if_none(cls, v, values):
        if v is None and 'documents' in values:
            return [str(uuid.uuid4()) for _ in range(len(values['documents']))]
        return v

class DocumentQueryRequest(BaseModel):
    query_texts: Optional[List[str]] = Field(None, description="List of query texts")
    query_embeddings: Optional[List[List[float]]] = Field(None, description="List of query embeddings")
    n_results: int = Field(10, description="Number of results to return per query")
    where: Optional[Dict[str, Any]] = Field(None, description="Filter condition for metadata")
    where_document: Optional[Dict[str, Any]] = Field(None, description="Filter condition for documents")
    
    @validator('query_texts', 'query_embeddings')
    def validate_query_input(cls, v, values, **kwargs):
        field_name = kwargs.get('field', None)
        other_field = 'query_embeddings' if field_name == 'query_texts' else 'query_texts'
        
        if field_name in values and other_field in values:
            if values[field_name] is None and values[other_field] is None:
                raise ValueError("Either query_texts or query_embeddings must be provided")
        
        return v

class DocumentQueryResponse(BaseModel):
    results: List[Dict[str, List[DocumentResponse]]] = Field(..., description="Query results")

# Reconciliation Models
class ReconciliationRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the collection to reconcile")
    scan_dir: Optional[str] = Field(None, description="Directory to scan for files")
    file_paths: Optional[List[str]] = Field(None, description="Specific file paths to reconcile")
    delete_missing: bool = Field(False, description="Whether to delete documents not found in filesystem")
    
    @validator('file_paths', 'scan_dir')
    def validate_input_paths(cls, v, values):
        if 'scan_dir' in values and values['scan_dir'] is None and 'file_paths' in values and values['file_paths'] is None:
            raise ValueError("Either scan_dir or file_paths must be provided")
        return v

class ReconciliationResponse(BaseModel):
    job_id: str = Field(..., description="ID of the reconciliation job")
    status: str = Field(..., description="Status of the reconciliation job")
    message: str = Field(..., description="Informational message about the job")

class ReconciliationStatusResponse(BaseModel):
    job_id: str = Field(..., description="ID of the reconciliation job")
    status: str = Field(..., description="Status of the job (e.g., running, completed, failed)")
    progress: float = Field(0, description="Progress percentage of the job")
    total_files: int = Field(0, description="Total number of files to process")
    processed_files: int = Field(0, description="Number of files processed so far")
    added_files: int = Field(0, description="Number of files added to vectorstore")
    updated_files: int = Field(0, description="Number of files updated in vectorstore")
    deleted_files: int = Field(0, description="Number of files deleted from vectorstore")
    errors: int = Field(0, description="Number of errors encountered")
    error_details: List[str] = Field([], description="List of error messages")
    start_time: Optional[datetime] = Field(None, description="Start time of the job")
    end_time: Optional[datetime] = Field(None, description="End time of the job (if completed)")
    collection_name: Optional[str] = Field(None, description="Name of the collection being reconciled")

class ReconciliationListResponse(BaseModel):
    jobs: List[ReconciliationStatusResponse] = Field(..., description="List of reconciliation jobs")

# Health Models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status (healthy/unhealthy)")
    version: str = Field(..., description="Service version")
    timestamp: float = Field(..., description="Current timestamp")
    uptime: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, Dict[str, Any]] = Field(..., description="Status of dependencies")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
