"""Chat and Question Answering endpoints powered by the RAG orchestrator."""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.errors import LLMServiceError, RetrievalError
from app.db.session import get_db
from app.embeddings import get_embedding_service
from app.llm import get_llm_service
from app.rag.orchestrator import RAGOrchestrator
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import get_reranker
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.retrieval import RetrievalQuery, RetrievalResponse

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a Contextual Question",
)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Contextual question answering over ingested documents with citations and provenance."""
    try:
        emb_service = get_embedding_service()
        llm_service = get_llm_service()
        orchestrator = RAGOrchestrator(
            db=db,
            embedding_service=emb_service,
            llm_service=llm_service,
        )
        return orchestrator.answer_query(request)
    except LLMServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM Gateway Error: {str(e)}",
        )
    except RetrievalError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval Error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


@router.post(
    "/retrieval/search",
    response_model=RetrievalResponse,
    summary="Inspect Hybrid Retrieval Scoring",
)
def search_retrieval(
    query_req: RetrievalQuery,
    db: Session = Depends(get_db),
):
    """Direct diagnostic endpoint to test semantic, keyword, and hybrid retrieval with reranking."""
    start_time = time.perf_counter()
    emb_service = get_embedding_service()
    retriever = HybridRetriever(
        db=db,
        embedding_service=emb_service,
        default_alpha=query_req.hybrid_alpha or 0.6,
    )

    candidates = retriever.retrieve(
        query=query_req.query,
        top_k=query_req.top_k * 2 if query_req.enable_reranking else query_req.top_k,
        alpha=query_req.hybrid_alpha,
        filters=query_req.filters,
    )

    if query_req.enable_reranking and candidates:
        reranker = get_reranker()
        final_results = reranker.rerank(
            query=query_req.query,
            candidates=candidates,
            top_n=query_req.top_k,
        )
    else:
        final_results = candidates[: query_req.top_k]

    latency = (time.perf_counter() - start_time) * 1000.0

    return RetrievalResponse(
        query=query_req.query,
        total_retrieved=len(final_results),
        results=final_results,
        latency_ms=round(latency, 2),
    )

