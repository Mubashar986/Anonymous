"""
REST API Router for Conversation and Message Endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies.auth import get_current_active_user, require_capability
from app.models.permission import CapabilityEnum
from app.models.user import User

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ParticipantResponse,
)
from app.services.conversation_service import conversation_service
from app.repositories.conversation_repository import conversation_repository

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _format_conversation_response(conv) -> ConversationResponse:
    participants = [
        ParticipantResponse(
            id=p.user.id,
            username=p.user.username,
            role=p.user.role,
        )
        for p in conv.participants
        if p.user
    ]
    return ConversationResponse(
        id=conv.id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        participants=participants,
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or retrieve a 1-to-1 conversation",
)
async def start_conversation(
    data: ConversationCreate,
    current_user: User = Depends(require_capability(CapabilityEnum.CAN_START_DIRECT_MESSAGE)),
    db: AsyncSession = Depends(get_db),
):

    conv = await conversation_service.start_conversation(
        db, current_user=current_user, target_user_id=data.target_user_id
    )
    return _format_conversation_response(conv)


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List active conversations for current user",
)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    convs = await conversation_service.list_user_conversations(
        db, current_user=current_user, skip=skip, limit=limit
    )
    items = [_format_conversation_response(c) for c in convs]
    return ConversationListResponse(items=items, skip=skip, limit=limit)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch conversation details",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_repository.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    is_part = await conversation_repository.is_participant(
        db, conversation_id, current_user.id
    )
    if not is_part:
        raise HTTPException(status_code=403, detail="Access denied")
    return _format_conversation_response(conv)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send direct message over REST",
)
async def send_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(require_capability(CapabilityEnum.CAN_SEND_DIRECT_MESSAGE)),
    db: AsyncSession = Depends(get_db),
):
    msg = await conversation_service.send_message(
        db,
        current_user=current_user,
        conversation_id=conversation_id,
        client_msg_id=data.client_msg_id,
        text=data.text,
    )
    return MessageResponse.model_validate(msg)


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch cursor-paginated chat history",
)
async def get_messages(
    conversation_id: uuid.UUID,
    before_timestamp: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await conversation_service.get_conversation_history(
        db,
        current_user=current_user,
        conversation_id=conversation_id,
        before_timestamp=before_timestamp,
        limit=limit,
    )
    items = [MessageResponse.model_validate(m) for m in messages]
    has_more = len(items) == limit
    return MessageListResponse(items=items, has_more=has_more)
