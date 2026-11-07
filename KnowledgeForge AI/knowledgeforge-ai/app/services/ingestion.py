"""Document ingestion, validation, parsing, chunking, and embedding indexing pipeline."""

import hashlib
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.core.errors import (
    DocumentNotFoundError,
    DocumentParsingError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.logging import logger
from app.embeddings.base import BaseEmbeddingService
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentDetailResponse, DocumentResponse
from app.services.chunking import ChunkerFactory
from app.services.parser import DocumentParserFactory


class DocumentIngestionService:
    """Manages document validation, parsing, intelligent chunking, and vector indexing."""

    def __init__(self, db: Session, embedding_service: BaseEmbeddingService):
        self.db = db
        self.embedding_service = embedding_service

    def validate_file(self, filename: str, file_size: int) -> None:
        """Validate filename extension and file size constraints."""
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File format '{ext}' is not supported. Allowed formats: {sorted(settings.ALLOWED_EXTENSIONS)}"
            )

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLargeError(
                f"File size {file_size / (1024 * 1024):.2f}MB exceeds the maximum allowed limit "
                f"of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

    def ingest_document(
        self,
        content: bytes,
        filename: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        chunking_strategy: Optional[str] = None,
    ) -> Document:
        """Process, chunk, embed, and index an uploaded document."""
        self.validate_file(filename, len(content))

        # Calculate SHA256 hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        # Check for existing document with same content hash
        existing = (
            self.db.query(Document)
            .filter(Document.file_hash == file_hash)
            .first()
        )
        if existing and existing.status == "indexed":
            logger.info(f"Document '{filename}' with hash {file_hash[:8]} already indexed.")
            return existing

        # Extract extension and initialize DB document record
        ext = Path(filename).suffix.lower()
        title = Path(filename).stem.replace("_", " ").title()

        doc = Document(
            title=title,
            filename=filename,
            file_type=ext.lstrip("."),
            file_size=len(content),
            file_hash=file_hash,
            status="processing",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        try:
            # 1. Parse document text and structural segments
            parser = DocumentParserFactory.get_parser(filename)
            parsed_doc = parser.parse(content, filename)

            # Update document title if extracted from metadata
            if parsed_doc.metadata.get("title"):
                doc.title = str(parsed_doc.metadata["title"])
            doc.doc_metadata = parsed_doc.metadata

            # 2. Intelligent Chunking
            strategy = chunking_strategy or settings.DEFAULT_CHUNKING_STRATEGY
            c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
            c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

            chunker = ChunkerFactory.get_chunker(
                strategy=strategy,
                chunk_size=c_size,
                chunk_overlap=c_overlap,
            )
            chunks = chunker.chunk_document(parsed_doc)

            if not chunks:
                raise DocumentParsingError("No textual content could be extracted from document.")

            # 3. Batch Embeddings Generation
            chunk_texts = [c.content for c in chunks]
            embeddings = self.embedding_service.embed_documents(chunk_texts)

            # 4. Save Chunks to Database
            db_chunks = []
            for idx, c in enumerate(chunks):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    token_count=c.token_count,
                    start_char=c.start_char,
                    end_char=c.end_char,
                    chunk_metadata=c.metadata,
                    embedding=embeddings[idx] if idx < len(embeddings) else None,
                )
                db_chunks.append(db_chunk)

            self.db.add_all(db_chunks)
            doc.chunk_count = len(db_chunks)
            doc.status = "indexed"
            doc.error_message = None
            self.db.commit()
            self.db.refresh(doc)

            logger.info(
                f"Successfully indexed document '{filename}' (ID: {doc.id}) with {len(db_chunks)} chunks."
            )
            return doc

        except Exception as e:
            logger.error(f"Failed to ingest document '{filename}': {e}", exc_info=True)
            doc.status = "failed"
            doc.error_message = str(e)
            self.db.commit()
            raise

    def get_document(self, document_id: str) -> Document:
        """Fetch a document by its unique ID."""
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' was not found.")
        return doc

    def list_documents(self, limit: int = 100, offset: int = 0) -> list[Document]:
        """List documents with pagination."""
        return (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_documents(self) -> int:
        """Return total number of registered documents."""
        return self.db.query(Document).count()

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks via cascade."""
        doc = self.get_document(document_id)
        self.db.delete(doc)
        self.db.commit()
        logger.info(f"Deleted document '{doc.title}' (ID: {document_id}) and all associated chunks.")
        return True

