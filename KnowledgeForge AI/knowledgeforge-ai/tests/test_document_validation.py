"""Tests for document validation and file integrity checking."""

import pytest
from app.core.errors import FileTooLargeError, UnsupportedFileTypeError
from app.services.ingestion import DocumentIngestionService


def test_allowed_file_types(db_session, mock_embedding_service):
    """Verify that supported extensions pass validation."""
    service = DocumentIngestionService(db=db_session, embedding_service=mock_embedding_service)

    # Allowed extensions
    for filename in ["manual.pdf", "policy.docx", "readme.txt", "notes.md", "CAPS.PDF"]:
        service.validate_file(filename, 1024)


def test_unsupported_file_types(db_session, mock_embedding_service):
    """Verify that unsupported extensions raise UnsupportedFileTypeError."""
    service = DocumentIngestionService(db=db_session, embedding_service=mock_embedding_service)

    unsupported = ["script.py", "archive.zip", "data.exe", "image.png", "sheet.xlsx"]
    for filename in unsupported:
        with pytest.raises(UnsupportedFileTypeError):
            service.validate_file(filename, 1024)


def test_file_size_limit(db_session, mock_embedding_service):
    """Verify that files exceeding the maximum size limit raise FileTooLargeError."""
    service = DocumentIngestionService(db=db_session, embedding_service=mock_embedding_service)

    # Within 25MB
    service.validate_file("document.pdf", 10 * 1024 * 1024)

    # Over 25MB (26MB)
    too_large = 26 * 1024 * 1024
    with pytest.raises(FileTooLargeError):
        service.validate_file("massive_file.pdf", too_large)

