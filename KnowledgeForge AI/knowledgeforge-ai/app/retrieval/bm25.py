"""BM25 lexical retrieval engine with small-corpus stabilization."""

import math
import re
from typing import Dict, List, Optional
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.document import Document, DocumentChunk
from app.schemas.retrieval import RetrievalFilter, RetrievalResult


class BM25Retriever:
    """Provides keyword-based search over document chunks using BM25."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple alphanumeric tokenizer with lowercasing."""
        if not text:
            return []
        return re.findall(r"\w+", text.lower())

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[RetrievalFilter] = None,
    ) -> List[RetrievalResult]:
        """Perform BM25 search on all indexed chunks."""
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                Document.title,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                DocumentChunk.chunk_metadata,
                Document.file_type,
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
        )

        if filters:
            if filters.document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(filters.document_ids))
            if filters.file_types:
                stmt = stmt.where(Document.file_type.in_(filters.file_types))

        rows = self.db.execute(stmt).all()
        if not rows:
            return []

        corpus = [self.tokenize(row[4]) for row in rows]
        query_set = set(query_tokens)

        # Compute BM25Okapi scores
        bm25 = BM25Okapi(corpus)
        # Floor negative / zero IDF values that occur on small corpora (N <= 3)
        for term, idf_val in bm25.idf.items():
            if idf_val <= 0.0:
                bm25.idf[term] = 0.25

        raw_scores = bm25.get_scores(query_tokens)

        # Also add a term overlap bonus to ensure exact matches score positively
        enhanced_scores = []
        for idx, doc_tokens in enumerate(corpus):
            overlap = len(query_set.intersection(set(doc_tokens)))
            overlap_score = overlap / max(1, len(query_set))
            combined = float(raw_scores[idx]) + (1.5 * overlap_score)
            enhanced_scores.append(combined)

        max_score = max(enhanced_scores) if enhanced_scores and max(enhanced_scores) > 0 else 1.0

        results: List[RetrievalResult] = []
        for idx, row in enumerate(rows):
            score = float(enhanced_scores[idx])
            if score <= 0.0:
                continue

            normalized_score = min(1.0, max(0.0, score / max_score))
            if filters and filters.min_score is not None and normalized_score < filters.min_score:
                continue

            chunk_id, doc_id, doc_title, chunk_idx, content, meta, f_type = row
            meta_dict = meta if isinstance(meta, dict) else {}

            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    document_title=doc_title,
                    chunk_index=chunk_idx,
                    content=content,
                    score=round(normalized_score, 4),
                    bm25_score=round(normalized_score, 4),
                    chunk_metadata=meta_dict,
                    page_number=meta_dict.get("page_number"),
                    section_header=meta_dict.get("section_header"),
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
