"""Prompt templates and context formatting for RAG generation."""

from typing import List, Optional
from app.schemas.retrieval import RetrievalResult

SYSTEM_RAG_PROMPT = """You are KnowledgeForge AI, an enterprise knowledge intelligence assistant.
Your mission is to provide accurate, truthful, and strictly grounded answers based exclusively on the provided reference context.

Strict Guidelines:
1. Base your answer ONLY on the information explicitly contained in the retrieved context passages below.
2. If the context does not contain sufficient facts to answer the question, you MUST clearly state: "Based on the provided documents, I do not have sufficient information to answer this question." Do NOT fabricate or assume missing details.
3. When referencing facts from a source, cite the source using the syntax: [Doc: <document_title>, Chunk: <chunk_index>] (e.g., [Doc: cloud_architecture.md, Chunk: 2]).
4. Maintain a professional, clear, and objective tone.
5. Do NOT treat previous assistant responses in conversational history as authoritative source evidence; only use the provided retrieved context.
"""


def format_context_passage(index: int, chunk: RetrievalResult) -> str:
    """Format an individual retrieved chunk into a standardized context block."""
    page_info = f", Page: {chunk.page_number}" if chunk.page_number is not None else ""
    section_info = f", Section: {chunk.section_header}" if chunk.section_header else ""
    return (
        f"[Source {index}] (Document: {chunk.document_title}, Chunk: {chunk.chunk_index}{page_info}{section_info})\n"
        f"Content: {chunk.content.strip()}"
    )


def assemble_rag_prompt(
    query: str,
    retrieved_chunks: List[RetrievalResult],
    conversation_history: Optional[List[dict]] = None,
) -> str:
    """Construct full prompt payload including retrieved passages and query."""
    if not retrieved_chunks:
        context_str = "No relevant context documents were retrieved."
    else:
        context_str = "\n\n".join(
            format_context_passage(idx, chunk)
            for idx, chunk in enumerate(retrieved_chunks, start=1)
        )

    history_str = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-4:]:  # last 4 turns
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.get('content', '').strip()}")
        history_str = "Prior Conversation Context (for conversational continuity only):\n" + "\n".join(history_lines) + "\n\n"

    prompt = (
        f"{history_str}"
        f"--- RETRIEVED CONTEXT START ---\n"
        f"{context_str}\n"
        f"--- RETRIEVED CONTEXT END ---\n\n"
        f"User Question: {query}\n\n"
        f"Answer with citations:"
    )
    return prompt

