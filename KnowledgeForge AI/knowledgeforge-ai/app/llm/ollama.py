"""Ollama LLM gateway for local models (e.g. Mistral, Llama 3)."""

from typing import Optional
import httpx
from app.core.errors import LLMServiceError
from app.core.logging import logger
from app.llm.base import BaseLLMService


class OllamaLLMService(BaseLLMService):
    """Integrates with a local Ollama instance for local LLM inference."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "mistral",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        timeout: float = 60.0,
    ):
        super().__init__(model_name=model_name, temperature=temperature, max_tokens=max_tokens)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code != 200:
                    raise LLMServiceError(
                        f"Ollama returned HTTP {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                msg = data.get("message", {}).get("content", "")
                if not msg:
                    raise LLMServiceError("Ollama returned an empty response.")
                return msg.strip()
        except httpx.ConnectError:
            raise LLMServiceError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Please ensure Ollama is installed and running (`ollama serve`), "
                f"and that model '{self.model_name}' has been pulled (`ollama pull {self.model_name}`)."
            )
        except Exception as e:
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(f"Ollama generation failed: {e}")

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

