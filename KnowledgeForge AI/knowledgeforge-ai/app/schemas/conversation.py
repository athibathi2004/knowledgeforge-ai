"""Pydantic schemas for conversation management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.chat import CitationItem


class ConversationMessageResponse(BaseModel):
    """Schema for an individual conversation message."""

    id: str
    conversation_id: str
    role: str
    content: str
    citations: Optional[List[CitationItem]] = None
    retrieval_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Schema for a conversation thread summary."""

    id: str
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """Schema for complete conversation thread with messages."""

    id: str
    title: str
    messages: List[ConversationMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Paginated or listed collection of conversations."""

    total: int
    conversations: List[ConversationResponse]

