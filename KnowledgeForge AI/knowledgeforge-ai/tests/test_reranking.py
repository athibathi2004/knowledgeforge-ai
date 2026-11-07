"""Tests for cross-encoder and ensemble reranking engines."""

import pytest
from app.retrieval.reranker import EnsembleReranker
from app.schemas.retrieval import RetrievalResult


def test_ensemble_reranker_phrase_promotion():
    """Verify that candidate containing exact query phrase receives higher rerank score."""
    reranker = EnsembleReranker()
    query = "Recovery Time Objective 15 minutes"

    candidates = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="General Cloud",
            chunk_index=0,
            content="Disaster recovery plans must document recovery time objectives for business tiers.",
            score=0.70,
        ),
        RetrievalResult(
            chunk_id="chunk-2",
            document_id="doc-2",
            document_title="Tier Specifications",
            chunk_index=1,
            content="The Recovery Time Objective 15 minutes applies to all Tier 1 mission-critical systems.",
            score=0.65,
        ),
    ]

    reranked = reranker.rerank(query, candidates, top_n=2)
    assert len(reranked) == 2
    # chunk-2 has exact phrase match and should be promoted to rank 1
    assert reranked[0].chunk_id == "chunk-2"
    assert reranked[0].rerank_score > reranked[1].rerank_score


def test_reranker_empty_candidates():
    """Verify reranker handles empty candidate list gracefully."""
    reranker = EnsembleReranker()
    assert reranker.rerank("some query", [], top_n=5) == []

