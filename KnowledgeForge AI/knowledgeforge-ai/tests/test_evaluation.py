"""Tests for RAGAS-compatible evaluation metrics and benchmark scoring."""

import pytest
from app.evaluation.metrics import RAGMetrics


def test_context_precision():
    """Verify context precision rewards ranking relevant contexts at top positions."""
    ground_truth_facts = ["RTO is 15 minutes", "RPO is under 1 minute"]

    # Relevant context at position 1
    high_precision_contexts = [
        "The RTO is 15 minutes and RPO is under 1 minute for cloud services.",
        "Unrelated text about office supplies.",
    ]
    score_high = RAGMetrics.compute_context_precision(high_precision_contexts, ground_truth_facts)

    # Relevant context at position 2
    low_precision_contexts = [
        "Unrelated text about office supplies.",
        "The RTO is 15 minutes and RPO is under 1 minute for cloud services.",
    ]
    score_low = RAGMetrics.compute_context_precision(low_precision_contexts, ground_truth_facts)

    assert score_high > score_low


def test_context_recall():
    """Verify context recall measures coverage of ground truth facts."""
    ground_truth_facts = ["AES-256 encryption required", "TLS 1.3 required"]

    full_contexts = ["We mandate AES-256 encryption for storage and TLS 1.3 for network."]
    partial_contexts = ["We mandate AES-256 encryption for storage."]

    recall_full = RAGMetrics.compute_context_recall(full_contexts, ground_truth_facts)
    recall_partial = RAGMetrics.compute_context_recall(partial_contexts, ground_truth_facts)

    assert recall_full == 1.0
    assert recall_partial < 1.0


def test_faithfulness_hallucination_penalty():
    """Verify faithfulness penalizes fabricated statements not supported by context."""
    context = ["The emergency command bridge must be convened within 5 minutes."]

    faithful_answer = "The emergency command bridge must be convened within 5 minutes."
    hallucinated_answer = (
        "The emergency command bridge must be convened within 5 minutes. "
        "All engineers must also wear yellow helmets and eat pizza."
    )

    score_faithful = RAGMetrics.compute_faithfulness(faithful_answer, context)
    score_hallucinated = RAGMetrics.compute_faithfulness(hallucinated_answer, context)

    assert score_faithful > score_hallucinated


def test_faithfulness_on_refusal():
    """Verify faithfulness is 1.0 when the system truthfully refuses due to missing information."""
    refusal = "Based on the provided documents, I do not have sufficient information to answer this question."
    score = RAGMetrics.compute_faithfulness(refusal, [])
    assert score == 1.0


def test_answer_relevance():
    """Verify answer relevance computes semantic and lexical alignment."""
    q = "What is the policy regarding customer data in LLM training?"
    relevant_a = "Customer data is strictly prohibited from being used to train foundation models."
    irrelevant_a = "The lunch cafeteria serves sandwiches on Tuesdays."

    rel_score = RAGMetrics.compute_answer_relevance(q, relevant_a)
    irrel_score = RAGMetrics.compute_answer_relevance(q, irrelevant_a)

    assert rel_score > irrel_score

