"""Pydantic schemas for RAG evaluation benchmarks."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationRunRequest(BaseModel):
    """Request to initiate an automated evaluation run."""

    dataset_path: Optional[str] = Field(
        default=None, description="Optional custom evaluation dataset path"
    )
    top_k: int = Field(default=5, ge=1, le=20)
    enable_reranking: bool = True


class EvaluationSampleResult(BaseModel):
    """Individual sample evaluation outcome."""

    question: str
    ground_truth_answer: str
    generated_answer: str
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevance: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    is_grounded: bool
    retrieved_chunk_ids: List[str] = Field(default_factory=list)


class EvaluationRunResponse(BaseModel):
    """Benchmark evaluation summary response."""

    id: str
    dataset_name: str
    sample_count: int
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevance: float
    mean_retrieval_latency_ms: float
    mean_generation_latency_ms: float
    detailed_results: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListResponse(BaseModel):
    """Collection of previous evaluation benchmark runs."""

    total: int
    runs: List[EvaluationRunResponse]

