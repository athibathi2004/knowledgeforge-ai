"""Logging configuration for KnowledgeForge AI."""

import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured logging for KnowledgeForge AI application."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("knowledgeforge")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        logger.addHandler(handler)

    # Suppress excessive logging from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.WARNING)

    return logger


logger = setup_logging()

