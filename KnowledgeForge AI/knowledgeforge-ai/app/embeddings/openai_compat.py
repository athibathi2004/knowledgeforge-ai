"""OpenAI-compatible embedding provider for remote or local inference gateways."""

from typing import List, Optional
import httpx
from app.core.errors import EmbeddingServiceError
from app.embeddings.base import BaseEmbeddingService


class OpenAICompatEmbeddingService(BaseEmbeddingService):
    """Generates embeddings using any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
        timeout: float = 30.0,
    ):
        super().__init__(model_name=model_name, dimension=dimension)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = f"{self.base_url}/embeddings"
        payload = {"model": self.model_name, "input": texts}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._get_headers(), json=payload)
                if resp.status_code != 200:
                    raise EmbeddingServiceError(
                        f"OpenAI embedding endpoint returned HTTP {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
        except Exception as e:
            if isinstance(e, EmbeddingServiceError):
                raise
            raise EmbeddingServiceError(f"OpenAI embedding request failed: {e}")

    def embed_query(self, text: str) -> List[float]:
        res = self.embed_documents([text])
        if not res:
            raise EmbeddingServiceError("No embedding returned for query")
        return res[0]

    def is_available(self) -> bool:
        if not self.api_key and "openai.com" in self.base_url:
            return False
        return True

