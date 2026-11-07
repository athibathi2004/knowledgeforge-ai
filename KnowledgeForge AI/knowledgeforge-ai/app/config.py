"""Application configuration for KnowledgeForge AI."""

import os
from pathlib import Path
from typing import List, Set
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for KnowledgeForge AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General App Information
    APP_NAME: str = "KnowledgeForge AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    # Defaults to local SQLite for instant out-of-the-box offline runs,
    # and seamlessly supports PostgreSQL with pgvector for production deployments.
    DATABASE_URL: str = "sqlite:///./knowledgeforge.db"

    # File Ingestion Settings
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt", ".md"}

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Chunking Strategy Configuration
    DEFAULT_CHUNK_SIZE: int = 600
    DEFAULT_CHUNK_OVERLAP: int = 120
    DEFAULT_CHUNKING_STRATEGY: str = "recursive"  # recursive, fixed, sliding_window

    # Embedding Service Configuration
    # Providers: "mock", "sentence_transformers", "ollama", "openai"
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_API_KEY: str = ""

    # LLM Gateway Configuration
    # Providers: "mock", "ollama", "openai"
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mistral"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024
    LLM_TIMEOUT: float = 60.0

    # Retrieval & Reranking Settings
    DEFAULT_TOP_K: int = 5
    HYBRID_ALPHA: float = 0.6  # 1.0 = pure vector, 0.0 = pure BM25
    ENABLE_RERANKING: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_N: int = 3
    MIN_RELEVANCE_SCORE: float = 0.20

    # Evaluation Benchmark Settings
    EVAL_DATASET_PATH: str = "sample-data/eval_dataset.json"

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()

# Ensure uploads directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

