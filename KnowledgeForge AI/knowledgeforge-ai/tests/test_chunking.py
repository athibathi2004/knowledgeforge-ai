"""Tests for intelligent chunking strategies and metadata preservation."""

import pytest
from app.services.chunking import (
    ChunkerFactory,
    FixedSizeChunker,
    RecursiveCharacterChunker,
    SlidingWindowChunker,
)
from app.services.parser import DocumentSegment, ParsedDocument


def test_recursive_character_chunker_sentence_splitting():
    """Verify recursive chunker splits on paragraph and sentence boundaries without breaking words."""
    text = (
        "First sentence regarding cloud infrastructure. "
        "Second sentence detailing database replication. "
        "Third sentence outlining encryption baselines.\n\n"
        "New paragraph describing incident command protocols. "
        "Fifth sentence on blameless post-mortem analysis."
    )
    chunker = RecursiveCharacterChunker(chunk_size=120, chunk_overlap=30)
    chunks = chunker.split_text(text)

    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.content) <= 150  # Respects chunk size limit
        assert c.token_count > 0
        assert c.end_char > c.start_char


def test_fixed_size_chunker():
    """Verify fixed-size chunker creates overlapping windows."""
    text = "A" * 500
    chunker = FixedSizeChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split_text(text)

    assert len(chunks) == 3
    assert chunks[0].content == "A" * 200
    assert chunks[1].content == "A" * 200
    assert len(chunks[2].content) <= 200


def test_sliding_window_chunker():
    """Verify token sliding window chunker."""
    words = [f"word{i}" for i in range(100)]
    text = " ".join(words)

    chunker = SlidingWindowChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split_text(text)

    assert len(chunks) >= 3
    assert all(c.token_count > 0 for c in chunks)


def test_chunking_preserves_document_segments():
    """Verify chunking a parsed document retains page and section metadata."""
    parsed_doc = ParsedDocument(
        filename="policy.pdf",
        file_type="pdf",
        full_text="Page 1 text.\n\nPage 2 text.",
        segments=[
            DocumentSegment(text="Page 1 content on security.", page_number=1, char_offset=0),
            DocumentSegment(text="Page 2 content on governance.", page_number=2, char_offset=30),
        ],
    )

    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document(parsed_doc)

    assert len(chunks) == 2
    assert chunks[0].metadata["page_number"] == 1
    assert chunks[1].metadata["page_number"] == 2
    assert chunks[0].metadata["filename"] == "policy.pdf"


def test_chunker_invalid_overlap():
    """Verify ValueError is raised if overlap exceeds chunk size."""
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=120)

