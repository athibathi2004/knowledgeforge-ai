"""CLI script to initialize KnowledgeForge AI database schema."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.db.init_db import init_db
from app.core.logging import logger

if __name__ == "__main__":
    logger.info("Starting database schema initialization...")
    init_db()
    logger.info("Initialization complete.")

