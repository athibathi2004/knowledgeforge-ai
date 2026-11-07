"""End-to-end RAG orchestrator coordinating retrieval, reranking, LLM generation, and citations."""

import time
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.core.logging import logger
from app.embeddings.base import BaseEmbeddingService
from app.llm.base import BaseLLMService
from app.models.conversation import Conversation, ConversationMessage
from app.rag.citations import CitationManager
from app.rag.prompts import SYSTEM_RAG_PROMPT, assemble_rag_prompt
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import BaseReranker, get_reranker
from app.schemas.chat import ChatRequest, ChatResponse, LatencyBreakdown
from app.schemas.retrieval import RetrievalResult


class RAGOrchestrator:
    """Coordinates the retrieval-augmented generation workflow."""

    def __init__(
        self,
        db: Session,
        embedding_service: BaseEmbeddingService,
        llm_service: BaseLLMService,
        reranker: Optional[BaseReranker] = None,
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.retriever = HybridRetriever(
            db=db,
            embedding_service=embedding_service,
            default_alpha=settings.HYBRID_ALPHA,
        )
        self.reranker = reranker or get_reranker(settings.RERANKER_MODEL)

    def _get_or_create_conversation(
        self, conversation_id: Optional[str], initial_query: str
    ) -> Conversation:
        """Retrieve existing conversation thread or create a new session."""
        if conversation_id:
            conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv:
                return conv

        # Create new conversation
        title = initial_query[:40] + ("..." if len(initial_query) > 40 else "")
        new_conv = Conversation(
            id=conversation_id or str(uuid.uuid4()),
            title=title,
        )
        self.db.add(new_conv)
        self.db.commit()
        self.db.refresh(new_conv)
        return new_conv

    def answer_query(self, request: ChatRequest) -> ChatResponse:
        """Execute end-to-end question answering pipeline."""
        total_start = time.perf_counter()
        query = request.query.strip()
        top_k = request.top_k or settings.DEFAULT_TOP_K

        # 1. Manage Conversation Session
        conv = self._get_or_create_conversation(request.conversation_id, query)

        # Retrieve prior turn history for conversational continuity
        prior_messages = (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conv.id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(6)
            .all()
        )
        conversation_history = [
            {"role": m.role, "content": m.content} for m in reversed(prior_messages)
        ]

        # 2. Hybrid Retrieval
        retrieval_start = time.perf_counter()
        initial_candidates = self.retriever.retrieve(
            query=query,
            top_k=top_k * 2 if request.enable_reranking else top_k,
            filters=request.filters,
        )
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0

        # 3. Reranking Stage
        rerank_start = time.perf_counter()
        if request.enable_reranking and initial_candidates:
            rerank_top_n = min(len(initial_candidates), top_k)
            retrieved_chunks = self.reranker.rerank(
                query=query,
                candidates=initial_candidates,
                top_n=rerank_top_n,
            )
        else:
            retrieved_chunks = initial_candidates[:top_k]
        rerank_latency = (time.perf_counter() - rerank_start) * 1000.0

        # 4. Context Grounding Check
        # If retrieved chunks have very low relevance or are empty, refuse to hallucinate
        max_score = max([c.score for c in retrieved_chunks], default=0.0)
        has_sufficient_context = len(retrieved_chunks) > 0 and max_score >= settings.MIN_RELEVANCE_SCORE

        # 5. LLM Prompt Assembly & Generation
        generation_start = time.perf_counter()
        if not has_sufficient_context:
            answer_text = (
                "Based on the provided documents, I do not have sufficient information "
                "to answer this question."
            )
            citations = []
            is_grounded = True
        else:
            prompt = assemble_rag_prompt(
                query=query,
                retrieved_chunks=retrieved_chunks,
                conversation_history=conversation_history,
            )
            raw_answer = self.llm_service.generate(
                prompt=prompt,
                system_prompt=SYSTEM_RAG_PROMPT,
            )
            answer_text = raw_answer.strip()
            # Extract and verify citations
            citations = CitationManager.process_citations(
                answer_text=answer_text,
                retrieved_chunks=retrieved_chunks,
            )
            is_grounded = len(citations) > 0 or "sufficient information" not in answer_text.lower()

        generation_latency = (time.perf_counter() - generation_start) * 1000.0
        total_latency = (time.perf_counter() - total_start) * 1000.0

        latency_breakdown = LatencyBreakdown(
            retrieval_ms=round(retrieval_latency, 2),
            rerank_ms=round(rerank_latency, 2),
            generation_ms=round(generation_latency, 2),
            total_ms=round(total_latency, 2),
        )

        # 6. Persist Conversation Turns
        user_msg = ConversationMessage(
            conversation_id=conv.id,
            role="user",
            content=query,
        )
        assistant_msg = ConversationMessage(
            conversation_id=conv.id,
            role="assistant",
            content=answer_text,
            citations=[c.model_dump() for c in citations],
            retrieval_metadata={
                "top_k": top_k,
                "latency_breakdown": latency_breakdown.model_dump(),
                "retrieved_chunk_count": len(retrieved_chunks),
            },
        )
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        self.db.commit()

        return ChatResponse(
            answer=answer_text,
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            citations=citations,
            sources=retrieved_chunks,
            latency=latency_breakdown,
            is_grounded=is_grounded,
        )

