"""Pydantic schemas for RAG chat and citations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.retrieval import RetrievalFilter, RetrievalResult


class CitationItem(BaseModel):
    """Structured citation referencing supporting document evidence."""

    source_id: str
    document_id: str
    document_title: str
    chunk_index: int
    page_number: Optional[int] = None
    section_header: Optional[str] = None
    snippet: str
    relevance_score: float


class LatencyBreakdown(BaseModel):
    """Detailed timing metrics for request stages in milliseconds."""

    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0


class ChatRequest(BaseModel):
    """User question answering request."""

    query: str = Field(..., min_length=1, description="User question or prompt")
    conversation_id: Optional[str] = Field(
        default=None, description="Optional conversation session ID"
    )
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    enable_reranking: Optional[bool] = Field(default=True)
    filters: Optional[RetrievalFilter] = None


class ChatResponse(BaseModel):
    """RAG answer with source citations and diagnostic metadata."""

    answer: str
    conversation_id: str
    message_id: str
    citations: List[CitationItem] = Field(default_factory=list)
    sources: List[RetrievalResult] = Field(default_factory=list)
    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    is_grounded: bool = True

