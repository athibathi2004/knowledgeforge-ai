"""Health check endpoint providing diagnostics on database, embeddings, and LLM services."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.embeddings import get_embedding_service
from app.llm import get_llm_service

router = APIRouter()


@router.get("/health", summary="System Health and Component Diagnostics")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Inspect and report health status of database, embedding service, and LLM provider."""
    # 1. Database Check
    db_healthy = False
    db_details = "Unknown"
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
        db_details = f"Connected ({db.bind.dialect.name if db.bind else 'sql'})"
    except Exception as e:
        db_details = f"Connection failed: {str(e)}"

    # 2. Embedding Service Check
    emb_service = get_embedding_service()
    emb_healthy = emb_service.is_available()

    # 3. LLM Gateway Check
    llm_service = get_llm_service()
    llm_healthy = llm_service.is_available()

    overall_status = "healthy" if (db_healthy and emb_healthy and llm_healthy) else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "details": db_details,
            },
            "embedding_service": {
                "provider": settings.EMBEDDING_PROVIDER,
                "model": settings.EMBEDDING_MODEL,
                "dimension": settings.EMBEDDING_DIMENSION,
                "ready": emb_healthy,
            },
            "llm_gateway": {
                "provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL,
                "ready": llm_healthy,
            },
        },
    }

