"""Abstract base class for LLM gateway providers."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMService(ABC):
    """Abstract interface for large language model generation."""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate response text given a user prompt and optional system instructions."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider service is reachable."""
        pass

