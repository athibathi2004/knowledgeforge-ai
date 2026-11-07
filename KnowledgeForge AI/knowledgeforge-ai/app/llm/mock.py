"""Deterministic, grounded mock LLM service for testing and offline environments."""

import re
from typing import List, Optional
from app.llm.base import BaseLLMService


class MockLLMService(BaseLLMService):
    """Grounded mock LLM that extracts facts directly from retrieved context blocks.

    Enforces strict RAG faithfulness:
    - If no relevant context is present, explicitly refuses to hallucinate.
    - If context is provided, extracts relevant factual sentences and attaches citations.
    """

    def __init__(
        self,
        model_name: str = "mock-generator",
        temperature: float = 0.0,
        max_tokens: int = 512,
    ):
        super().__init__(model_name=model_name, temperature=temperature, max_tokens=max_tokens)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        # Check if the prompt contains assembled context
        if "--- RETRIEVED CONTEXT START ---" not in prompt:
            return "Based on the provided documents, I do not have sufficient information to answer this question."

        # Extract context section and query
        context_part = prompt.split("--- RETRIEVED CONTEXT START ---")[1].split(
            "--- RETRIEVED CONTEXT END ---"
        )[0]

        query = ""
        if "User Question:" in prompt:
            query = prompt.split("User Question:")[1].strip()

        # Parse source blocks
        # Format in prompt: [Source 1] (Document: filename, Chunk: idx, Page: p) \n Content: ...
        source_blocks = re.findall(
            r"\[Source (\d+)\] \(Document: ([^,]+), Chunk: (\d+)(?:, Page: ([^)]+))?\)\nContent: (.*?)(?=\n\n\[Source|\Z)",
            context_part,
            re.DOTALL,
        )

        if not source_blocks:
            return "Based on the provided documents, I do not have sufficient information to answer this question."

        query_terms = set(re.findall(r"\w{3,}", query.lower()))
        matched_sentences: List[str] = []
        citations_used = []

        for src_num, doc_title, chunk_idx, page_num, content in source_blocks:
            doc_title = doc_title.strip()
            sentences = re.split(r"(?<=[.?!]) +", content.strip())
            relevant_sentences = []

            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean:
                    continue
                sent_words = set(re.findall(r"\w{3,}", sent_clean.lower()))
                if query_terms and (query_terms.intersection(sent_words)):
                    relevant_sentences.append(sent_clean)

            if relevant_sentences:
                page_str = f", Page: {page_num.strip()}" if page_num and page_num.strip() != "None" else ""
                citation = f"[Doc: {doc_title}, Chunk: {chunk_idx}{page_str}]"
                matched_sentences.extend(relevant_sentences[:2])
                citations_used.append(citation)

        if not matched_sentences:
            return "Based on the provided documents, I do not have sufficient information to answer this question."

        # Synthesize coherent grounded answer
        answer_body = " ".join(matched_sentences[:4])
        unique_citations = list(dict.fromkeys(citations_used))
        citation_suffix = " " + " ".join(unique_citations)

        return f"{answer_body}{citation_suffix}"

    def is_available(self) -> bool:
        return True

