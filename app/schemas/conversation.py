"""
Pydantic Schemas for Conversations and Messages.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import WS_MAX_TEXT_LEN


class ConversationCreate(BaseModel):
    target_user_id: uuid.UUID


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: str


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantResponse]


class MessageCreate(BaseModel):
    client_msg_id: uuid.UUID
    text: str = Field(..., min_length=1, max_length=WS_MAX_TEXT_LEN)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    client_msg_id: uuid.UUID
    text: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    has_more: bool = False


class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    skip: int = 0
    limit: int = 20
