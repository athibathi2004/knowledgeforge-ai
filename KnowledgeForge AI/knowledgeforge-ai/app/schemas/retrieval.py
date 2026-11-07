"""Pydantic schemas for search and retrieval."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalFilter(BaseModel):
    """Optional metadata filters for targeted retrieval."""

    document_ids: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    min_score: Optional[float] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class RetrievalResult(BaseModel):
    """A single retrieved chunk with scoring and attribution metadata."""

    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    score: float
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rerank_score: Optional[float] = None
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    page_number: Optional[int] = None
    section_header: Optional[str] = None


class RetrievalQuery(BaseModel):
    """Schema for direct retrieval requests."""

    query: str = Field(..., min_length=1, description="Search query string")
    top_k: int = Field(default=5, ge=1, le=50)
    hybrid_alpha: Optional[float] = Field(default=0.6, ge=0.0, le=1.0)
    enable_reranking: bool = True
    filters: Optional[RetrievalFilter] = None


class RetrievalResponse(BaseModel):
    """Response containing retrieved candidates and retrieval diagnostics."""

    query: str
    total_retrieved: int
    results: List[RetrievalResult]
    latency_ms: float

