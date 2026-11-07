"""Base SQLAlchemy declarative model and custom types."""

from datetime import datetime, timezone
import json
from typing import Any
from sqlalchemy import DateTime, TypeDecorator, Text
from sqlalchemy.orm import DeclarativeBase


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


class SafeJSON(TypeDecorator):
    """Platform-independent JSON type that works on SQLite and PostgreSQL."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

