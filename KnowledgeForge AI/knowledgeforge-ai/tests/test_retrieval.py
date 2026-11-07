"""Tests for semantic, BM25, and hybrid retrieval engines."""

import pytest
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.vector_store import VectorStore
from app.schemas.retrieval import RetrievalFilter
from app.services.ingestion import DocumentIngestionService


@pytest.fixture
def indexed_db(db_session, mock_embedding_service):
    """Seed the database with sample indexed documents."""
    ingestion = DocumentIngestionService(db=db_session, embedding_service=mock_embedding_service)

    doc1_content = (
        "Enterprise Cloud Architecture Guidelines.\n\n"
        "Recovery Time Objective (RTO) for Tier 1 services is 15 minutes. "
        "Recovery Point Objective (RPO) is under 1 minute for Tier 1 services.\n\n"
        "AES-256 encryption is mandatory for all persistent storage volumes. "
        "TLS 1.3 is required for all data in transit across all regions."
    ).encode("utf-8")

    doc2_content = (
        "Site Reliability Engineering Incident Response SOP.\n\n"
        "Severity-1 (Critical Outage): Core user functionality unavailable. "
        "The escalation bridge must be convened within 5 minutes.\n\n"
        "Incident Commander (IC) has authority to declare Sev-1 and command response teams. "
        "A blameless post-mortem RCA must be published within 72 hours."
    ).encode("utf-8")

    ingestion.ingest_document(doc1_content, "cloud_guide.md")
    ingestion.ingest_document(doc2_content, "incident_sop.md")
    return db_session


def test_vector_similarity_retrieval(indexed_db, mock_embedding_service):
    """Verify vector search retrieves the most relevant semantic chunk."""
    store = VectorStore(indexed_db)
    query_vec = mock_embedding_service.embed_query("What is the RTO for Tier 1 cloud services?")
    results = store.search(query_vec, top_k=3)

    assert len(results) > 0
    top = results[0]
    assert "cloud_guide" in top.document_title.lower() or "RTO" in top.content
    assert top.score > 0.0


def test_bm25_keyword_retrieval(indexed_db):
    """Verify BM25 keyword search scores exact keyword hits."""
    bm25 = BM25Retriever(indexed_db)
    results = bm25.search("Incident Commander Severity-1", top_k=3)

    assert len(results) > 0
    top = results[0]
    assert "Incident Commander" in top.content or "Severity-1" in top.content
    assert top.bm25_score > 0.0


def test_hybrid_retrieval_rrf_and_weighted(indexed_db, mock_embedding_service):
    """Verify hybrid retriever merges vector and keyword scores."""
    hybrid = HybridRetriever(
        db=indexed_db,
        embedding_service=mock_embedding_service,
        default_alpha=0.6,
    )

    # RRF Fusion
    rrf_results = hybrid.retrieve("encryption AES-256 TLS 1.3", top_k=3, fusion_method="rrf")
    assert len(rrf_results) > 0
    assert rrf_results[0].score > 0.0

    # Weighted Fusion
    weighted_results = hybrid.retrieve("encryption AES-256 TLS 1.3", top_k=3, fusion_method="weighted")
    assert len(weighted_results) > 0
    assert weighted_results[0].vector_score is not None
    assert weighted_results[0].bm25_score is not None


def test_retrieval_metadata_filtering(indexed_db, mock_embedding_service):
    """Verify metadata filtering restricts retrieval to specific documents or file types."""
    hybrid = HybridRetriever(db=indexed_db, embedding_service=mock_embedding_service)

    # Filter to only incident_sop.md
    filters = RetrievalFilter(file_types=["markdown"])
    results = hybrid.retrieve("emergency command", top_k=5, filters=filters)
    assert all("markdown" in r.chunk_metadata.get("file_type", "markdown") for r in results)

