"""CLI script to ingest all synthetic demonstration files from sample-data/."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.core.logging import logger
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.embeddings import get_embedding_service
from app.services.ingestion import DocumentIngestionService


def ingest_all_samples():
    """Ingest sample data files into KnowledgeForge AI knowledge base."""
    init_db()
    db = SessionLocal()
    try:
        emb_service = get_embedding_service()
        ingestion = DocumentIngestionService(db=db, embedding_service=emb_service)

        sample_dir = root_dir / "sample-data"
        supported_exts = {".md", ".pdf", ".docx", ".txt"}
        files = [p for p in sample_dir.iterdir() if p.suffix.lower() in supported_exts]

        print(f"\n=======================================================")
        print(f" KnowledgeForge AI - Automated Sample Data Ingestion")
        print(f"=======================================================")
        print(f"Found {len(files)} demonstration files in {sample_dir}\n")

        total_chunks = 0
        for f in files:
            content = f.read_bytes()
            print(f"-> Ingesting {f.name} ({len(content) / 1024:.1f} KB)...", end=" ")
            doc = ingestion.ingest_document(
                content=content,
                filename=f.name,
            )
            print(f"OK [Chunks: {doc.chunk_count}, Status: {doc.status}]")
            total_chunks += doc.chunk_count

        print(f"\nIngestion Complete! Total Indexed Chunks: {total_chunks}")
        print(f"Documents are now ready for semantic and hybrid retrieval queries.\n")

    finally:
        db.close()


if __name__ == "__main__":
    ingest_all_samples()

