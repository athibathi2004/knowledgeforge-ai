"""Database initialization and schema migration helpers."""

from sqlalchemy import text
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine
import app.models  # Ensure all models are imported before creating tables


def init_db() -> None:
    """Initialize the database schema."""
    logger.info("Initializing database tables...")

    # If running PostgreSQL, attempt to create pgvector extension if available
    if engine.dialect.name == "postgresql":
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("PostgreSQL pgvector extension verified or created.")
        except Exception as e:
            logger.warning(f"Could not initialize pgvector extension: {e}")

    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    init_db()

