"""Vector store abstraction supporting PostgreSQL/pgvector and in-memory NumPy fallback."""

import math
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.document import Document, DocumentChunk
from app.schemas.retrieval import RetrievalFilter, RetrievalResult


class VectorStore:
    """Manages vector persistence and semantic similarity retrieval."""

    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[RetrievalFilter] = None,
    ) -> List[RetrievalResult]:
        """Perform semantic cosine similarity search over indexed chunks."""
        query_vec = np.array(query_embedding, dtype=np.float32)
        norm_q = np.linalg.norm(query_vec)
        if norm_q > 0:
            query_vec = query_vec / norm_q

        # Build base query joining Document for metadata filtering
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                Document.title,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                DocumentChunk.chunk_metadata,
                DocumentChunk.embedding,
                Document.file_type,
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
        )

        # Apply metadata filters
        if filters:
            if filters.document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(filters.document_ids))
            if filters.file_types:
                stmt = stmt.where(Document.file_type.in_(filters.file_types))

        rows = self.db.execute(stmt).all()
        if not rows:
            return []

        candidates = []
        for row in rows:
            chunk_id, doc_id, doc_title, chunk_idx, content, meta, emb, f_type = row
            if not emb:
                continue

            try:
                emb_arr = np.array(emb, dtype=np.float32)
                norm_e = np.linalg.norm(emb_arr)
                if norm_e > 0:
                    emb_arr = emb_arr / norm_e
                # Cosine similarity
                cosine_sim = float(np.dot(query_vec, emb_arr))
                # Map [-1, 1] to [0, 1]
                normalized_score = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0))
            except Exception as e:
                logger.warning(f"Error computing similarity for chunk {chunk_id}: {e}")
                continue

            if filters and filters.min_score is not None and normalized_score < filters.min_score:
                continue

            meta_dict = meta if isinstance(meta, dict) else {}
            candidates.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    document_title=doc_title,
                    chunk_index=chunk_idx,
                    content=content,
                    score=round(normalized_score, 4),
                    vector_score=round(normalized_score, 4),
                    chunk_metadata=meta_dict,
                    page_number=meta_dict.get("page_number"),
                    section_header=meta_dict.get("section_header"),
                )
            )

        # Sort descending by similarity score
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]

