"""Tests for vector embedding generation and consistency."""

import math
import numpy as np
import pytest
from app.embeddings.mock import MockEmbeddingService


def test_mock_embedding_dimension_and_normalization():
    """Verify generated embeddings match dimension and are unit normalized."""
    dim = 128
    service = MockEmbeddingService(dimension=dim)
    vec = service.embed_query("Enterprise cloud architecture and disaster recovery.")

    assert len(vec) == dim
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4


def test_mock_embedding_determinism():
    """Verify that identical input strings produce strictly identical vectors."""
    service = MockEmbeddingService(dimension=64)
    text = "Recovery Time Objective (RTO) for mission critical workloads."
    vec1 = service.embed_query(text)
    vec2 = service.embed_query(text)

    assert vec1 == vec2


def test_mock_embedding_semantic_similarity():
    """Verify that semantically related texts have higher cosine similarity than unrelated texts."""
    service = MockEmbeddingService(dimension=256)
    q = service.embed_query("cloud disaster recovery RTO objective")
    doc_similar = service.embed_query("recovery time objective RTO target for cloud disaster recovery")
    doc_unrelated = service.embed_query("culinary chocolate cookie baking temperature oven recipe")

    sim_similar = float(np.dot(q, doc_similar))
    sim_unrelated = float(np.dot(q, doc_unrelated))

    assert sim_similar > sim_unrelated


def test_mock_embedding_batch():
    """Verify batch document embedding returns the correct number of vectors."""
    service = MockEmbeddingService(dimension=64)
    texts = ["doc one", "doc two", "doc three"]
    embeddings = service.embed_documents(texts)

    assert len(embeddings) == 3
    assert all(len(e) == 64 for e in embeddings)

