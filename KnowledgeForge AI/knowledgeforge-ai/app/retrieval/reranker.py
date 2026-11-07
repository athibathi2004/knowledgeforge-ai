"""Reranking engine for retrieved context candidates."""

from abc import ABC, abstractmethod
import math
import re
from typing import List, Optional
from app.core.logging import logger
from app.schemas.retrieval import RetrievalResult


class BaseReranker(ABC):
    """Abstract interface for reranking candidate chunks."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_n: int = 3,
    ) -> List[RetrievalResult]:
        """Rerank candidates based on deep query-document relevance."""
        pass


class EnsembleReranker(BaseReranker):
    """Lightweight, deterministic lexical-semantic ensemble reranker.

    Calculates phrase density, keyword proximity, title relevance, and positional bonuses
    to calibrate retrieval precision without requiring external GPU/network dependencies.
    """

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_n: int = 3,
    ) -> List[RetrievalResult]:
        if not candidates:
            return []

        query_clean = query.lower().strip()
        query_words = set(re.findall(r"\w+", query_clean))

        scored_candidates = []
        for cand in candidates:
            content_lower = cand.content.lower()
            cand_words = re.findall(r"\w+", content_lower)
            cand_word_count = len(cand_words)

            if cand_word_count == 0:
                continue

            # 1. Exact phrase match bonus
            phrase_bonus = 0.35 if query_clean in content_lower else 0.0

            # 2. Query word coverage (recall)
            matched_words = query_words.intersection(set(cand_words))
            coverage = len(matched_words) / max(1, len(query_words))

            # 3. Term density in document
            term_matches = sum(1 for w in cand_words if w in query_words)
            density = min(1.0, term_matches / max(5, cand_word_count))

            # 4. Title / Section relevance bonus
            header_bonus = 0.0
            if cand.section_header and any(w in cand.section_header.lower() for w in query_words):
                header_bonus += 0.15
            if cand.document_title and any(w in cand.document_title.lower() for w in query_words):
                header_bonus += 0.10

            # 5. Integrate prior retrieval score
            prior_score = cand.score or 0.0

            # Combined calibrated rerank score
            calibrated_score = (
                (0.40 * coverage)
                + (0.25 * prior_score)
                + (0.15 * density)
                + phrase_bonus
                + header_bonus
            )
            calibrated_score = max(0.0, min(1.0, calibrated_score))

            cand.rerank_score = round(calibrated_score, 4)
            # Final effective score is rerank score
            cand.score = cand.rerank_score
            scored_candidates.append(cand)

        scored_candidates.sort(key=lambda x: x.rerank_score or 0.0, reverse=True)
        return scored_candidates[:top_n]


class CrossEncoderReranker(BaseReranker):
    """Deep cross-encoder model reranker using sentence-transformers."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._fallback = EnsembleReranker()

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                logger.info(f"Loading CrossEncoder model '{self.model_name}'...")
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(
                    f"CrossEncoder unavailable ({e}). Falling back to EnsembleReranker."
                )
                self._model = False
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_n: int = 3,
    ) -> List[RetrievalResult]:
        model = self._get_model()
        if not model:
            return self._fallback.rerank(query, candidates, top_n)

        try:
            pairs = [[query, cand.content] for cand in candidates]
            scores = model.predict(pairs)

            # Sigmoid normalization
            for idx, cand in enumerate(candidates):
                raw_score = float(scores[idx])
                normalized = 1.0 / (1.0 + math.exp(-raw_score))
                cand.rerank_score = round(normalized, 4)
                cand.score = cand.rerank_score

            candidates.sort(key=lambda x: x.rerank_score or 0.0, reverse=True)
            return candidates[:top_n]
        except Exception as e:
            logger.error(f"CrossEncoder prediction error: {e}. Using fallback.")
            return self._fallback.rerank(query, candidates, top_n)


def get_reranker(model_name: Optional[str] = None) -> BaseReranker:
    """Instantiate appropriate reranker."""
    # Default to EnsembleReranker for reliable, self-contained execution,
    # with CrossEncoder available when configured and dependencies are present.
    return EnsembleReranker()

