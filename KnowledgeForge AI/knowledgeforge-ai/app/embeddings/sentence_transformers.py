"""Sentence Transformers local embedding provider."""

from typing import List, Optional
from app.core.errors import EmbeddingServiceError
from app.core.logging import logger
from app.embeddings.base import BaseEmbeddingService


class SentenceTransformersEmbeddingService(BaseEmbeddingService):
    """Local embedding service powered by HuggingFace / sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        super().__init__(model_name=model_name, dimension=dimension)
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading local SentenceTransformer model '{self.model_name}'...")
                self._model = SentenceTransformer(self.model_name)
                # Calibrate actual output dimension
                sample_emb = self._model.encode("test", normalize_embeddings=True)
                self.dimension = len(sample_emb)
            except ImportError:
                raise EmbeddingServiceError(
                    "sentence-transformers is not installed. Run 'pip install sentence-transformers' "
                    "or configure EMBEDDING_PROVIDER=mock in your .env file."
                )
            except Exception as e:
                raise EmbeddingServiceError(
                    f"Failed to load SentenceTransformer model '{self.model_name}': {e}"
                )
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        try:
            embeddings = model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            raise EmbeddingServiceError(f"Error encoding document batch: {e}")

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        try:
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingServiceError(f"Error encoding query: {e}")

    def is_available(self) -> bool:
        try:
            self._get_model()
            return True
        except Exception:
            return False

