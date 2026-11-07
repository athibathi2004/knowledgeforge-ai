"""Ollama embedding provider for local open-source models."""

from typing import List
import httpx
from app.core.errors import EmbeddingServiceError
from app.core.logging import logger
from app.embeddings.base import BaseEmbeddingService


class OllamaEmbeddingService(BaseEmbeddingService):
    """Generates vector embeddings using a local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "nomic-embed-text",
        dimension: int = 768,
        timeout: float = 30.0,
    ):
        super().__init__(model_name=model_name, dimension=dimension)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def embed_query(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                if response.status_code != 200:
                    raise EmbeddingServiceError(
                        f"Ollama returned HTTP {response.status_code}: {response.text}"
                    )
                data = response.json()
                embedding = data.get("embedding")
                if not embedding:
                    raise EmbeddingServiceError("Ollama response did not contain 'embedding'")
                return embedding
        except httpx.ConnectError:
            raise EmbeddingServiceError(
                f"Ollama embedding service is unreachable at {self.base_url}. "
                "Ensure Ollama is running (`ollama serve`) and the model is downloaded (`ollama pull "
                f"{self.model_name}`)."
            )
        except Exception as e:
            if isinstance(e, EmbeddingServiceError):
                raise
            raise EmbeddingServiceError(f"Ollama embedding request failed: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Ollama /api/embeddings processes one prompt per request
        embeddings: List[List[float]] = []
        for text in texts:
            embeddings.append(self.embed_query(text))
        return embeddings

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

