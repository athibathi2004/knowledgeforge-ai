"""Document parsers for PDF, DOCX, TXT, and Markdown files."""

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf
import docx
from app.core.errors import DocumentParsingError, UnsupportedFileTypeError
from app.core.logging import logger
from app.services.preprocessing import TextPreprocessor


@dataclass
class DocumentSegment:
    """Represents a structural segment of a document (e.g. a page or section)."""

    text: str
    page_number: Optional[int] = None
    section_header: Optional[str] = None
    char_offset: int = 0


@dataclass
class ParsedDocument:
    """Extracted document content and metadata."""

    filename: str
    file_type: str
    full_text: str
    segments: List[DocumentSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDocumentParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        """Parse raw file bytes into a structured ParsedDocument."""
        pass


class PDFDocumentParser(BaseDocumentParser):
    """Extracts text, metadata, and page numbers from PDF files using pypdf."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            segments: List[DocumentSegment] = []
            full_text_parts: List[str] = []
            char_offset = 0

            pdf_meta = reader.metadata or {}
            metadata = {
                "title": pdf_meta.get("/Title") or Path(filename).stem,
                "author": pdf_meta.get("/Author"),
                "producer": pdf_meta.get("/Producer"),
                "page_count": len(reader.pages),
            }

            for page_idx, page in enumerate(reader.pages, start=1):
                raw_page_text = page.extract_text() or ""
                cleaned_page_text = TextPreprocessor.preprocess(raw_page_text)
                if cleaned_page_text:
                    segments.append(
                        DocumentSegment(
                            text=cleaned_page_text,
                            page_number=page_idx,
                            char_offset=char_offset,
                        )
                    )
                    full_text_parts.append(cleaned_page_text)
                    char_offset += len(cleaned_page_text) + 2

            full_text = "\n\n".join(full_text_parts)
            return ParsedDocument(
                filename=filename,
                file_type="pdf",
                full_text=full_text,
                segments=segments,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to parse PDF document {filename}: {e}", exc_info=True)
            raise DocumentParsingError(f"PDF extraction failed for {filename}: {str(e)}")


class DocxDocumentParser(BaseDocumentParser):
    """Extracts text and hierarchical headings from DOCX files using python-docx."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            doc = docx.Document(io.BytesIO(content))
            segments: List[DocumentSegment] = []
            full_text_parts: List[str] = []
            current_section = "General"
            current_section_texts: List[str] = []
            char_offset = 0

            # Inspect core properties
            metadata = {
                "title": doc.core_properties.title or Path(filename).stem,
                "author": doc.core_properties.author,
                "category": doc.core_properties.category,
                "paragraph_count": len(doc.paragraphs),
            }

            for para in doc.paragraphs:
                cleaned_text = TextPreprocessor.preprocess(para.text)
                if not cleaned_text:
                    continue

                if para.style and para.style.name and para.style.name.startswith("Heading"):
                    if current_section_texts:
                        section_body = "\n\n".join(current_section_texts)
                        segments.append(
                            DocumentSegment(
                                text=section_body,
                                section_header=current_section,
                                char_offset=char_offset,
                            )
                        )
                        char_offset += len(section_body) + 2
                        current_section_texts = []
                    current_section = cleaned_text

                current_section_texts.append(cleaned_text)
                full_text_parts.append(cleaned_text)

            # Flush trailing section
            if current_section_texts:
                section_body = "\n\n".join(current_section_texts)
                segments.append(
                    DocumentSegment(
                        text=section_body,
                        section_header=current_section,
                        char_offset=char_offset,
                    )
                )

            full_text = "\n\n".join(full_text_parts)
            return ParsedDocument(
                filename=filename,
                file_type="docx",
                full_text=full_text,
                segments=segments,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to parse DOCX document {filename}: {e}", exc_info=True)
            raise DocumentParsingError(f"DOCX extraction failed for {filename}: {str(e)}")


class TextDocumentParser(BaseDocumentParser):
    """Extracts text from UTF-8/plain text and Markdown files."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            # Attempt decoding with UTF-8, fall back to latin-1
            try:
                raw_text = content.decode("utf-8")
            except UnicodeDecodeError:
                raw_text = content.decode("latin-1")

            cleaned_text = TextPreprocessor.preprocess(raw_text)
            ext = Path(filename).suffix.lower()
            file_type = "markdown" if ext == ".md" else "text"

            segments = [
                DocumentSegment(
                    text=cleaned_text,
                    section_header="Document Content",
                    char_offset=0,
                )
            ]

            metadata = {
                "title": Path(filename).stem.replace("_", " ").title(),
                "file_type": file_type,
                "character_count": len(cleaned_text),
                "line_count": len(cleaned_text.splitlines()),
            }

            return ParsedDocument(
                filename=filename,
                file_type=file_type,
                full_text=cleaned_text,
                segments=segments,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to parse text document {filename}: {e}", exc_info=True)
            raise DocumentParsingError(f"Text parsing failed for {filename}: {str(e)}")


class DocumentParserFactory:
    """Factory to get the appropriate document parser for a given file extension."""

    _parsers = {
        ".pdf": PDFDocumentParser,
        ".docx": DocxDocumentParser,
        ".txt": TextDocumentParser,
        ".md": TextDocumentParser,
    }

    @classmethod
    def get_parser(cls, filename: str) -> BaseDocumentParser:
        ext = Path(filename).suffix.lower()
        parser_cls = cls._parsers.get(ext)
        if not parser_cls:
            raise UnsupportedFileTypeError(
                f"Unsupported file format '{ext}'. Supported formats: {list(cls._parsers.keys())}"
            )
        return parser_cls()

