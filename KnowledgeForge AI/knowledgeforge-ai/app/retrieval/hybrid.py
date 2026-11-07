"""Hybrid retrieval engine combining semantic vector search and BM25 keyword search."""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.embeddings.base import BaseEmbeddingService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore
from app.schemas.retrieval import RetrievalFilter, RetrievalResult


class HybridRetriever:
    """Orchestrates hybrid retrieval with Reciprocal Rank Fusion (RRF) and weighted fusion."""

    def __init__(
        self,
        db: Session,
        embedding_service: BaseEmbeddingService,
        default_alpha: float = 0.6,
        rrf_k: int = 60,
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.default_alpha = default_alpha
        self.rrf_k = rrf_k
        self.vector_store = VectorStore(db)
        self.bm25_retriever = BM25Retriever(db)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        alpha: Optional[float] = None,
        filters: Optional[RetrievalFilter] = None,
        fusion_method: str = "rrf",  # 'rrf' or 'weighted'
    ) -> List[RetrievalResult]:
        """Perform hybrid search over indexed document chunks.

        Args:
            query: User search text.
            top_k: Number of candidates to return.
            alpha: Weight for vector retrieval (0.0 to 1.0).
            filters: Optional metadata filtering criteria.
            fusion_method: Fusion algorithm ('rrf' for Reciprocal Rank Fusion or 'weighted').
        """
        effective_alpha = self.default_alpha if alpha is None else alpha
        candidate_pool_size = max(top_k * 3, 20)

        # 1. Vector Search
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=candidate_pool_size,
            filters=filters,
        )

        # 2. BM25 Keyword Search
        bm25_results = self.bm25_retriever.search(
            query=query,
            top_k=candidate_pool_size,
            filters=filters,
        )

        # Index candidates by chunk_id
        chunk_map: Dict[str, RetrievalResult] = {}
        for r in vector_results:
            chunk_map[r.chunk_id] = r
        for r in bm25_results:
            if r.chunk_id not in chunk_map:
                chunk_map[r.chunk_id] = r

        if not chunk_map:
            return []

        # 3. Fusion Ranking
        final_scores: Dict[str, float] = {}

        if fusion_method == "rrf":
            # Reciprocal Rank Fusion
            for rank, r in enumerate(vector_results, start=1):
                final_scores[r.chunk_id] = final_scores.get(r.chunk_id, 0.0) + (
                    effective_alpha / (self.rrf_k + rank)
                )

            for rank, r in enumerate(bm25_results, start=1):
                final_scores[r.chunk_id] = final_scores.get(r.chunk_id, 0.0) + (
                    (1.0 - effective_alpha) / (self.rrf_k + rank)
                )

            # Normalize RRF scores into 0-1 range
            max_rrf = max(final_scores.values()) if final_scores else 1.0
            for cid in final_scores:
                final_scores[cid] = final_scores[cid] / max_rrf
        else:
            # Weighted linear score combination
            vec_score_map = {r.chunk_id: r.score for r in vector_results}
            bm25_score_map = {r.chunk_id: r.score for r in bm25_results}

            for cid in chunk_map:
                v_score = vec_score_map.get(cid, 0.0)
                b_score = bm25_score_map.get(cid, 0.0)
                final_scores[cid] = (effective_alpha * v_score) + ((1.0 - effective_alpha) * b_score)

        # 4. Attach detailed component scores to results
        vec_score_lookup = {r.chunk_id: r.score for r in vector_results}
        bm25_score_lookup = {r.chunk_id: r.score for r in bm25_results}

        ranked_results: List[RetrievalResult] = []
        for chunk_id, fused_score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True):
            item = chunk_map[chunk_id]
            item.score = round(fused_score, 4)
            item.vector_score = round(vec_score_lookup.get(chunk_id, 0.0), 4)
            item.bm25_score = round(bm25_score_lookup.get(chunk_id, 0.0), 4)
            ranked_results.append(item)

        return ranked_results[:top_k]

