"""Pydantic schemas for documents and chunks."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunkResponse(BaseModel):
    """Schema for a document chunk."""

    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    start_char: int
    end_char: int
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    """Schema for document summary response."""

    id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    file_hash: str
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response including chunk preview."""

    chunks: List[DocumentChunkResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    """Paginated or listed collection of documents."""

    total: int
    documents: List[DocumentResponse]

