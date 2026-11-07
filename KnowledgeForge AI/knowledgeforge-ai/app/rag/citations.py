"""Citation extraction, verification, and source snippet mapping."""

import re
from typing import Dict, List, Optional, Set
from app.schemas.chat import CitationItem
from app.schemas.retrieval import RetrievalResult


class CitationManager:
    """Extracts, verifies, and constructs structured citation objects from LLM answers."""

    @staticmethod
    def extract_snippet(chunk_content: str, max_chars: int = 240) -> str:
        """Extract a representative preview snippet from a chunk."""
        if not chunk_content:
            return ""
        cleaned = re.sub(r"\s+", " ", chunk_content.strip())
        if len(cleaned) <= max_chars:
            return cleaned
        # Find clean sentence or word boundary
        cutoff = cleaned[:max_chars].rfind(". ")
        if cutoff > 80:
            return cleaned[: cutoff + 1]
        return cleaned[:max_chars].rstrip() + "..."

    @classmethod
    def process_citations(
        cls,
        answer_text: str,
        retrieved_chunks: List[RetrievalResult],
    ) -> List[CitationItem]:
        """Extract citation references from the answer and map them to retrieved chunks."""
        if not retrieved_chunks:
            return []

        chunk_by_idx: Dict[int, RetrievalResult] = {}
        chunk_by_doc_chunk: Dict[str, RetrievalResult] = {}

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            chunk_by_idx[idx] = chunk
            # Key format: (document_title_lower, chunk_index)
            doc_key = f"{chunk.document_title.lower()}:{chunk.chunk_index}"
            chunk_by_doc_chunk[doc_key] = chunk

        matched_chunks: List[RetrievalResult] = []
        seen_chunk_ids: Set[str] = set()

        # 1. Match [Doc: <title>, Chunk: <idx>] patterns
        doc_matches = re.findall(
            r"\[Doc:\s*([^,\]]+),\s*Chunk:\s*(\d+)(?:,\s*Page:\s*[^\]]+)?\]",
            answer_text,
            re.IGNORECASE,
        )
        for doc_title, chunk_idx_str in doc_matches:
            target_key = f"{doc_title.strip().lower()}:{int(chunk_idx_str)}"
            chunk = chunk_by_doc_chunk.get(target_key)
            if chunk and chunk.chunk_id not in seen_chunk_ids:
                matched_chunks.append(chunk)
                seen_chunk_ids.add(chunk.chunk_id)

        # 2. Match [Source <num>] or [Source: <num>] patterns
        src_matches = re.findall(r"\[Source:?\s*(\d+)\]", answer_text, re.IGNORECASE)
        for num_str in src_matches:
            num = int(num_str)
            chunk = chunk_by_idx.get(num)
            if chunk and chunk.chunk_id not in seen_chunk_ids:
                matched_chunks.append(chunk)
                seen_chunk_ids.add(chunk.chunk_id)

        # 3. Fallback: If no explicit inline citation brackets were found, but the model
        # generated an answer citing facts, link the top-scoring retrieved chunk
        if not matched_chunks and retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            # Only attribute if top chunk has high relevance
            if top_chunk.score >= 0.40:
                matched_chunks.append(top_chunk)

        # Build CitationItem objects
        citations: List[CitationItem] = []
        for chunk in matched_chunks:
            citations.append(
                CitationItem(
                    source_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    section_header=chunk.section_header,
                    snippet=cls.extract_snippet(chunk.content),
                    relevance_score=chunk.score,
                )
            )

        return citations

