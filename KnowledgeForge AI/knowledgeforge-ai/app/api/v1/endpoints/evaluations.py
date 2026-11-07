"""API endpoints for automated RAG quality and retrieval evaluation benchmarks."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.embeddings import get_embedding_service
from app.evaluation.dataset import EvaluationDataset
from app.evaluation.evaluator import RAGEvaluator
from app.llm import get_llm_service
from app.models.evaluation import EvaluationRun
from app.rag.orchestrator import RAGOrchestrator
from app.schemas.evaluation import (
    EvaluationListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)

router = APIRouter()


@router.post(
    "/evaluations/run",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Evaluation Benchmark",
)
def run_evaluation_benchmark(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
):
    """Trigger automated RAGAS-compatible benchmark over test dataset."""
    dataset_path = request.dataset_path or settings.EVAL_DATASET_PATH
    dataset = EvaluationDataset.from_json(dataset_path)

    emb_service = get_embedding_service()
    llm_service = get_llm_service()
    orchestrator = RAGOrchestrator(
        db=db,
        embedding_service=emb_service,
        llm_service=llm_service,
    )
    evaluator = RAGEvaluator(db=db, orchestrator=orchestrator)

    eval_run = evaluator.evaluate_dataset(
        dataset=dataset,
        top_k=request.top_k,
        enable_reranking=request.enable_reranking,
    )
    return eval_run


@router.get(
    "/evaluations/results",
    response_model=EvaluationListResponse,
    summary="List Benchmark Evaluation Results",
)
def list_evaluation_results(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve history of evaluation runs with precision, recall, faithfulness, and latency scores."""
    runs = (
        db.query(EvaluationRun)
        .order_by(EvaluationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(EvaluationRun).count()
    return EvaluationListResponse(total=total, runs=runs)


@router.get(
    "/evaluations/results/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get Specific Benchmark Run Details",
)
def get_evaluation_run(
    run_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed sample-level results for a specific evaluation run."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' was not found.",
        )
    return run

