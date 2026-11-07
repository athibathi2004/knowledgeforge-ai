"""Abstract base class for embedding providers."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingService(ABC):
    """Abstract interface for document and query vector embedding generation."""

    def __init__(self, model_name: str, dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute vector embeddings for a list of document texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Compute vector embedding for a single query text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the embedding service backend is currently reachable and ready."""
        pass

