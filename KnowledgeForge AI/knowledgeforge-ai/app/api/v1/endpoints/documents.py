"""API endpoints for document ingestion, retrieval, and lifecycle management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.errors import (
    DocumentNotFoundError,
    DocumentParsingError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.db.session import get_db
from app.embeddings import get_embedding_service
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.ingestion import DocumentIngestionService

router = APIRouter()


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Index a Document",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (.pdf, .docx, .txt, .md)"),
    chunk_size: Optional[int] = Form(None, description="Target chunk size in characters"),
    chunk_overlap: Optional[int] = Form(None, description="Overlap between consecutive chunks"),
    chunking_strategy: Optional[str] = Form(None, description="recursive, fixed, or sliding_window"),
    db: Session = Depends(get_db),
):
    """Upload a supported document for text extraction, chunking, and vector embedding."""
    try:
        content = await file.read()
        emb_service = get_embedding_service()
        ingestion_service = DocumentIngestionService(db=db, embedding_service=emb_service)

        doc = ingestion_service.ingest_document(
            content=content,
            filename=file.filename or "uploaded_document",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy,
        )
        return doc
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except DocumentParsingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during ingestion: {str(e)}",
        )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List All Indexed Documents",
)
def list_documents(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve all indexed documents with pagination and chunk count summaries."""
    emb_service = get_embedding_service()
    ingestion_service = DocumentIngestionService(db=db, embedding_service=emb_service)
    docs = ingestion_service.list_documents(limit=limit, offset=offset)
    total = ingestion_service.count_documents()
    return DocumentListResponse(total=total, documents=docs)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get Document Details and Chunks",
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Fetch full document metadata along with all extracted semantic chunks."""
    emb_service = get_embedding_service()
    ingestion_service = DocumentIngestionService(db=db, embedding_service=emb_service)
    try:
        doc = ingestion_service.get_document(document_id)
        return doc
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Remove a document and purge all associated vector chunks from the index."""
    emb_service = get_embedding_service()
    ingestion_service = DocumentIngestionService(db=db, embedding_service=emb_service)
    try:
        ingestion_service.delete_document(document_id)
        return {"message": f"Document '{document_id}' successfully deleted."}
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

