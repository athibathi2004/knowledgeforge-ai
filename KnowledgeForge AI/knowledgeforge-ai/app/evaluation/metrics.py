"""RAGAS-compatible evaluation metrics computation."""

import math
import re
from typing import List, Set


class RAGMetrics:
    """Computes RAG evaluation metrics without external proprietary dependencies."""

    @staticmethod
    def _extract_tokens(text: str) -> Set[str]:
        if not text:
            return set()
        # Extract alphanumeric words and acronyms
        return set(re.findall(r"[a-zA-Z0-9]{2,}", text.lower()))

    @classmethod
    def compute_context_precision(
        cls,
        retrieved_contexts: List[str],
        ground_truth_facts: List[str],
    ) -> float:
        """Measure whether relevant chunks are ranked higher in the retrieved list.

        Calculates Mean Average Precision (MAP) over the ranked retrieved chunks.
        """
        if not retrieved_contexts or not ground_truth_facts:
            return 0.0

        num_hits = 0
        precision_at_k_sum = 0.0

        for rank, context in enumerate(retrieved_contexts, start=1):
            ctx_tokens = cls._extract_tokens(context)
            # Check if this context contains any of the ground truth facts
            is_relevant = False
            for fact in ground_truth_facts:
                fact_tokens = cls._extract_tokens(fact)
                if not fact_tokens:
                    continue
                overlap = len(fact_tokens.intersection(ctx_tokens))
                # Consider relevant if >= 40% of key tokens are present in context
                if overlap / len(fact_tokens) >= 0.40:
                    is_relevant = True
                    break

            if is_relevant:
                num_hits += 1
                precision_at_k_sum += num_hits / rank

        if num_hits == 0:
            return 0.0
        return round(precision_at_k_sum / num_hits, 4)

    @classmethod
    def compute_context_recall(
        cls,
        retrieved_contexts: List[str],
        ground_truth_facts: List[str],
    ) -> float:
        """Measure what fraction of ground truth facts are covered by the retrieved contexts."""
        if not ground_truth_facts:
            return 1.0
        if not retrieved_contexts:
            return 0.0

        all_context_tokens = cls._extract_tokens(" ".join(retrieved_contexts))
        covered_facts = 0

        for fact in ground_truth_facts:
            fact_tokens = cls._extract_tokens(fact)
            if not fact_tokens:
                continue
            overlap = len(fact_tokens.intersection(all_context_tokens))
            if overlap / len(fact_tokens) >= 0.45:
                covered_facts += 1

        return round(covered_facts / len(ground_truth_facts), 4)

    @classmethod
    def compute_faithfulness(
        cls,
        generated_answer: str,
        retrieved_contexts: List[str],
    ) -> float:
        """Measure if claims in the generated answer are grounded in the retrieved context.

        Penalizes fabricated statements and hallucinated entities.
        """
        if not generated_answer:
            return 0.0

        # If answer explicitly acknowledges missing information, it is faithful
        if "sufficient information" in generated_answer.lower():
            return 1.0

        if not retrieved_contexts:
            return 0.0

        # Split answer into candidate factual statements / sentences
        statements = [
            s.strip()
            for s in re.split(r"(?<=[.?!]) +", generated_answer)
            if len(s.strip()) > 15 and not s.strip().startswith("[Doc:")
        ]
        if not statements:
            return 1.0

        all_context_text = " ".join(retrieved_contexts).lower()
        supported_statements = 0

        for stmt in statements:
            stmt_tokens = cls._extract_tokens(stmt)
            if not stmt_tokens:
                continue
            tokens_in_ctx = sum(1 for t in stmt_tokens if t in all_context_text)
            support_ratio = tokens_in_ctx / len(stmt_tokens)
            if support_ratio >= 0.55:
                supported_statements += 1

        return round(supported_statements / len(statements), 4)

    @classmethod
    def compute_answer_relevance(
        cls,
        question: str,
        generated_answer: str,
    ) -> float:
        """Measure semantic alignment between user question and generated answer."""
        q_tokens = cls._extract_tokens(question)
        if not q_tokens:
            return 1.0
        a_tokens = cls._extract_tokens(generated_answer)
        if not a_tokens:
            return 0.0

        intersection = len(q_tokens.intersection(a_tokens))
        union = len(q_tokens.union(a_tokens))
        jaccard = intersection / max(1, union)
        overlap = intersection / len(q_tokens)

        score = (0.7 * overlap) + (0.3 * jaccard)
        return round(min(1.0, max(0.0, score)), 4)
