"""SQLAlchemy model for evaluation benchmark runs."""

import uuid
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, SafeJSON, utc_now


class EvaluationRun(Base):
    """Represents a benchmark evaluation execution record."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Core RAGAS-compatible aggregate metrics
    context_precision: Mapped[float] = mapped_column(Float, default=0.0)
    context_recall: Mapped[float] = mapped_column(Float, default=0.0)
    faithfulness: Mapped[float] = mapped_column(Float, default=0.0)
    answer_relevance: Mapped[float] = mapped_column(Float, default=0.0)

    # Latency benchmarks
    mean_retrieval_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    mean_generation_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Granular sample-level breakdown
    detailed_results: Mapped[dict] = mapped_column(SafeJSON, default=dict)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    def __repr__(self) -> str:
        return f"<EvaluationRun id={self.id} samples={self.sample_count} faithfulness={self.faithfulness:.2f}>"

