"""Embedding service factory and provider exports."""

from app.config import settings
from app.embeddings.base import BaseEmbeddingService
from app.embeddings.mock import MockEmbeddingService
from app.embeddings.sentence_transformers import SentenceTransformersEmbeddingService
from app.embeddings.ollama import OllamaEmbeddingService
from app.embeddings.openai_compat import OpenAICompatEmbeddingService


def get_embedding_service(
    provider: str | None = None,
    model_name: str | None = None,
) -> BaseEmbeddingService:
    """Factory to instantiate and return the configured embedding service."""
    selected_provider = (provider or settings.EMBEDDING_PROVIDER).lower()
    selected_model = model_name or settings.EMBEDDING_MODEL

    if selected_provider == "sentence_transformers":
        return SentenceTransformersEmbeddingService(
            model_name=selected_model,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    elif selected_provider == "ollama":
        return OllamaEmbeddingService(
            base_url=settings.EMBEDDING_BASE_URL,
            model_name=selected_model,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    elif selected_provider == "openai":
        return OpenAICompatEmbeddingService(
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY,
            model_name=selected_model,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    else:
        # Default fallback to deterministic mock embedding service
        return MockEmbeddingService(
            model_name=selected_model,
            dimension=settings.EMBEDDING_DIMENSION,
        )


__all__ = [
    "BaseEmbeddingService",
    "MockEmbeddingService",
    "SentenceTransformersEmbeddingService",
    "OllamaEmbeddingService",
    "OpenAICompatEmbeddingService",
    "get_embedding_service",
]

