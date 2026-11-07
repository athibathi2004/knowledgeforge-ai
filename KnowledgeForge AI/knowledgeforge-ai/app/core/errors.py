"""Domain exceptions and error models for KnowledgeForge AI."""

from typing import Any, Dict, Optional


class KnowledgeForgeError(Exception):
    """Base exception class for KnowledgeForge AI."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentNotFoundError(KnowledgeForgeError):
    """Raised when a requested document is not found."""
    pass


class UnsupportedFileTypeError(KnowledgeForgeError):
    """Raised when an uploaded file has an unsupported format or MIME type."""
    pass


class FileTooLargeError(KnowledgeForgeError):
    """Raised when an uploaded file exceeds the configured size limit."""
    pass


class DocumentParsingError(KnowledgeForgeError):
    """Raised when document content extraction fails."""
    pass


class EmbeddingServiceError(KnowledgeForgeError):
    """Raised when embedding generation fails or embedding service is unavailable."""
    pass


class LLMServiceError(KnowledgeForgeError):
    """Raised when LLM invocation fails or model endpoint is unreachable."""
    pass


class RetrievalError(KnowledgeForgeError):
    """Raised when hybrid retrieval or vector similarity search fails."""
    pass


class ConversationNotFoundError(KnowledgeForgeError):
    """Raised when a requested conversation thread is not found."""
    pass


class EvaluationError(KnowledgeForgeError):
    """Raised when evaluation benchmark execution fails."""
    pass

