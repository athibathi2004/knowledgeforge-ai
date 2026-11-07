"""Main v1 API router assembling all domain endpoint routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    documents,
    chat,
    conversations,
    evaluations,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(documents.router, tags=["Documents"])
api_router.include_router(chat.router, tags=["Chat & RAG"])
api_router.include_router(conversations.router, tags=["Conversations"])
api_router.include_router(evaluations.router, tags=["Evaluations"])

