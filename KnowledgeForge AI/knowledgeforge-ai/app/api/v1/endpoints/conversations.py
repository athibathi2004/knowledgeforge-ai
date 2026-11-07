"""API endpoints for conversation session history and multi-turn state."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.conversation import Conversation
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
)

router = APIRouter()


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List Conversations",
)
def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve list of conversation threads ordered by last updated timestamp."""
    threads = (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(Conversation).count()

    summaries = []
    for conv in threads:
        summaries.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                message_count=len(conv.messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return ConversationListResponse(total=total, conversations=summaries)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get Conversation Messages",
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full conversation history including turns, citations, and metadata."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found.",
        )
    return conv


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Conversation",
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """Delete a conversation thread and its message history."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' was not found.",
        )
    db.delete(conv)
    db.commit()
    return {"message": f"Conversation '{conversation_id}' deleted successfully."}

