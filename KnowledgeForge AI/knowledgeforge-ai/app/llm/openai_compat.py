"""OpenAI-compatible LLM gateway for vLLM, LMStudio, LocalAI, or remote endpoints."""

from typing import Optional
import httpx
from app.core.errors import LLMServiceError
from app.core.logging import logger
from app.llm.base import BaseLLMService


class OpenAICompatLLMService(BaseLLMService):
    """Integrates with any OpenAI-compatible completions API endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "",
        model_name: str = "mistral",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        timeout: float = 60.0,
    ):
        super().__init__(model_name=model_name, temperature=temperature, max_tokens=max_tokens)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._get_headers(), json=payload)
                if resp.status_code != 200:
                    raise LLMServiceError(
                        f"LLM endpoint returned HTTP {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMServiceError("No completion choices returned by LLM endpoint.")
                return choices[0].get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            raise LLMServiceError(
                f"Cannot connect to OpenAI-compatible endpoint at {self.base_url}. "
                "Verify host and port configuration in .env."
            )
        except Exception as e:
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(f"OpenAI-compatible LLM generation failed: {e}")

    def is_available(self) -> bool:
        if not self.api_key and "openai.com" in self.base_url:
            return False
        return True

