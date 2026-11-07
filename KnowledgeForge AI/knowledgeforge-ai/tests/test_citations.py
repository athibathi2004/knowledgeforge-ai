"""Tests for citation extraction, source verification, and provenance."""

import pytest
from app.rag.citations import CitationManager
from app.schemas.retrieval import RetrievalResult


@pytest.fixture
def sample_retrieved_chunks():
    return [
        RetrievalResult(
            chunk_id="chk-001",
            document_id="doc-001",
            document_title="cloud_guide.md",
            chunk_index=0,
            content="Recovery Time Objective (RTO) for Tier 1 services is 15 minutes. RPO is under 1 minute.",
            score=0.92,
            page_number=1,
            section_header="Disaster Recovery",
        ),
        RetrievalResult(
            chunk_id="chk-002",
            document_id="doc-002",
            document_title="incident_sop.md",
            chunk_index=2,
            content="Severity-1 incident escalation bridge must be convened within 5 minutes.",
            score=0.85,
            page_number=2,
            section_header="Incident Roles",
        ),
    ]


def test_parse_doc_chunk_citations(sample_retrieved_chunks):
    """Verify parsing [Doc: <title>, Chunk: <idx>] citations."""
    answer = (
        "Tier 1 services have an RTO of 15 minutes [Doc: cloud_guide.md, Chunk: 0]. "
        "Sev-1 escalation bridges must convene in 5 minutes [Doc: incident_sop.md, Chunk: 2]."
    )
    citations = CitationManager.process_citations(answer, sample_retrieved_chunks)

    assert len(citations) == 2
    assert citations[0].document_title == "cloud_guide.md"
    assert citations[0].chunk_index == 0
    assert citations[0].page_number == 1
    assert citations[1].document_title == "incident_sop.md"
    assert citations[1].chunk_index == 2


def test_parse_source_number_citations(sample_retrieved_chunks):
    """Verify parsing [Source 1] citations."""
    answer = "The recovery objective is strictly 15 minutes [Source 1]."
    citations = CitationManager.process_citations(answer, sample_retrieved_chunks)

    assert len(citations) == 1
    assert citations[0].source_id == "chk-001"
    assert "Recovery Time Objective" in citations[0].snippet


def test_snippet_extraction():
    """Verify snippet extraction cleanly respects sentence boundaries."""
    long_content = "First sentence is concise. Second sentence has more detailed facts about infrastructure. Third sentence."
    snippet = CitationManager.extract_snippet(long_content, max_chars=60)
    assert len(snippet) <= 65
    assert snippet.endswith("...") or snippet.endswith(".")

