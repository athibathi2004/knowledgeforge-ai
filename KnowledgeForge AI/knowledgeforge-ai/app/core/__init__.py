"""Core module for KnowledgeForge AI."""

from app.core.logging import logger, setup_logging
from app.core.errors import (
    KnowledgeForgeError,
    DocumentNotFoundError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentParsingError,
    EmbeddingServiceError,
    LLMServiceError,
    RetrievalError,
    ConversationNotFoundError,
    EvaluationError,
)

__all__ = [
    "logger",
    "setup_logging",
    "KnowledgeForgeError",
    "DocumentNotFoundError",
    "UnsupportedFileTypeError",
    "FileTooLargeError",
    "DocumentParsingError",
    "EmbeddingServiceError",
    "LLMServiceError",
    "RetrievalError",
    "ConversationNotFoundError",
    "EvaluationError",
]

