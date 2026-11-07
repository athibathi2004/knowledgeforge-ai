"""Tests for document parsing and text extraction engines."""

from pathlib import Path
import pytest
from app.services.parser import DocumentParserFactory, TextDocumentParser, PDFDocumentParser, DocxDocumentParser
from app.services.preprocessing import TextPreprocessor


def test_text_preprocessor_normalization():
    """Verify whitespace cleaning, control character removal, and NFKC unicode normalization."""
    raw = "Header \xa0 Text \r\n\r\n\r\n  Subtext with \x00 null and spaces.   "
    cleaned = TextPreprocessor.preprocess(raw)
    assert "\xa0" not in cleaned
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "Header Text\n\nSubtext with null and spaces." == cleaned


def test_text_and_markdown_parser():
    """Verify parsing plain text and markdown files."""
    parser = TextDocumentParser()
    md_content = b"# Architecture Overview\n\nThis is a sample markdown document."
    parsed = parser.parse(md_content, "arch.md")

    assert parsed.file_type == "markdown"
    assert "Architecture Overview" in parsed.full_text
    assert len(parsed.segments) == 1
    assert parsed.metadata["line_count"] >= 2


def test_pdf_parser_on_sample():
    """Verify PDF extraction preserves page numbers and text."""
    pdf_path = Path(__file__).resolve().parent.parent / "sample-data" / "incident_response_sop.pdf"
    if not pdf_path.exists():
        pytest.skip("Sample PDF not found.")

    parser = PDFDocumentParser()
    content = pdf_path.read_bytes()
    parsed = parser.parse(content, "incident_response_sop.pdf")

    assert parsed.file_type == "pdf"
    assert len(parsed.segments) == 2
    assert parsed.segments[0].page_number == 1
    assert parsed.segments[1].page_number == 2
    assert "Severity-1" in parsed.full_text
    assert "Incident Commander" in parsed.full_text


def test_docx_parser_on_sample():
    """Verify DOCX extraction preserves section headers and text."""
    docx_path = Path(__file__).resolve().parent.parent / "sample-data" / "ai_governance_policy.docx"
    if not docx_path.exists():
        pytest.skip("Sample DOCX not found.")

    parser = DocxDocumentParser()
    content = docx_path.read_bytes()
    parsed = parser.parse(content, "ai_governance_policy.docx")

    assert parsed.file_type == "docx"
    assert "Corporate Responsible AI" in parsed.full_text
    assert len(parsed.segments) >= 1
    assert any(s.section_header for s in parsed.segments)


def test_parser_factory_dispatch():
    """Verify DocumentParserFactory dispatches appropriate parser instances."""
    assert isinstance(DocumentParserFactory.get_parser("test.pdf"), PDFDocumentParser)
    assert isinstance(DocumentParserFactory.get_parser("test.docx"), DocxDocumentParser)
    assert isinstance(DocumentParserFactory.get_parser("test.txt"), TextDocumentParser)
    assert isinstance(DocumentParserFactory.get_parser("test.md"), TextDocumentParser)

