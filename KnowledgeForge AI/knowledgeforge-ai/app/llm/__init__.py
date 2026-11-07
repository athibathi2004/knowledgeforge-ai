"""LLM Gateway factory and exports."""

from app.config import settings
from app.llm.base import BaseLLMService
from app.llm.mock import MockLLMService
from app.llm.ollama import OllamaLLMService
from app.llm.openai_compat import OpenAICompatLLMService


def get_llm_service(
    provider: str | None = None,
    model_name: str | None = None,
) -> BaseLLMService:
    """Factory returning the configured LLM provider service."""
    selected_provider = (provider or settings.LLM_PROVIDER).lower()
    selected_model = model_name or settings.LLM_MODEL

    if selected_provider == "ollama":
        return OllamaLLMService(
            base_url=settings.LLM_BASE_URL,
            model_name=selected_model,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
        )
    elif selected_provider == "openai":
        return OpenAICompatLLMService(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model_name=selected_model,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
        )
    else:
        # Default mock LLM provider
        return MockLLMService(
            model_name=selected_model,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )


__all__ = [
    "BaseLLMService",
    "MockLLMService",
    "OllamaLLMService",
    "OpenAICompatLLMService",
    "get_llm_service",
]

