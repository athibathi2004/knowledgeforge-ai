"""Deterministic, offline embedding provider for testing and zero-dependency environments."""

import hashlib
import math
import re
from typing import List
from app.embeddings.base import BaseEmbeddingService


class MockEmbeddingService(BaseEmbeddingService):
    """Generates deterministic pseudo-semantic vector embeddings without external network or heavy models.

    Uses bag-of-words and character n-gram hashing projected onto a normalized unit sphere,
    ensuring that semantically similar texts yield higher cosine similarities than unrelated texts.
    """

    def __init__(self, model_name: str = "mock-minilm", dimension: int = 384):
        super().__init__(model_name=model_name, dimension=dimension)

    def _generate_vector(self, text: str) -> List[float]:
        """Convert text into a deterministic, normalized float vector of length `self.dimension`."""
        if not text:
            return [0.0] * self.dimension

        vec = [0.0] * self.dimension
        tokens = re.findall(r"\w+", text.lower())

        # Bag-of-words projection
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = token_hash % self.dimension
            sign = 1.0 if ((token_hash >> 8) & 1) else -1.0
            vec[idx] += sign * 1.5

        # Character trigrams for morphological similarity
        cleaned = re.sub(r"\s+", " ", text.lower().strip())
        for i in range(len(cleaned) - 2):
            trigram = cleaned[i : i + 3]
            tri_hash = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
            idx = tri_hash % self.dimension
            sign = 1.0 if ((tri_hash >> 4) & 1) else -1.0
            vec[idx] += sign * 0.5

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [round(x / norm, 6) for x in vec]
        return [0.0] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def is_available(self) -> bool:
        return True

