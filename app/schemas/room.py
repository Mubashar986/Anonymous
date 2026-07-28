"""
Pydantic schemas for Community Rooms, Room Requests, and Administrative Actions.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.room import RoomRequestStatus


class RoomRequestCreate(BaseModel):
    """Request body for submitting a room creation request."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Proposed room name (1-50 characters).",
        examples=["Python Devs Lounge"],
    )
    is_private: bool = Field(
        default=False,
        description="True if room should require an active subscription.",
    )


class RoomRequestApprove(BaseModel):
    """Request body for admin room request approval with optional name override."""
    final_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional final name overriding requested name upon approval.",
    )


class RoomRequestResponse(BaseModel):
    """Response body representing a single RoomRequest entity."""
    id: uuid.UUID
    requester_id: uuid.UUID
    name: str
    is_private: bool
    status: RoomRequestStatus
    decision_by_id: Optional[uuid.UUID] = None
    decision_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoomCreateDirect(BaseModel):
    """Request body for direct room creation by administrators."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Globally unique room name.",
    )
    is_private: bool = Field(
        default=False,
        description="True if room is restricted to subscribers.",
    )


class RoomResponse(BaseModel):
    """Response body representing a single Room entity."""
    id: uuid.UUID
    name: str
    is_private: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    is_joined: Optional[bool] = False

    model_config = {"from_attributes": True}


class RoomApproveResponse(BaseModel):
    """Response body returned when an administrator approves a room request."""
    request: RoomRequestResponse
    room: RoomResponse


class RoomListResponse(BaseModel):
    """Paginated list of community rooms."""
    items: List[RoomResponse]
    total: int


class RoomRequestListResponse(BaseModel):
    """Paginated list of room requests."""
    items: List[RoomRequestResponse]
    total: int


class RoomMemberResponse(BaseModel):
    """Response body representing a single RoomMember entity."""
    id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    removed_at: Optional[datetime] = None
    removed_by_id: Optional[uuid.UUID] = None
    username: Optional[str] = None

    model_config = {"from_attributes": True}


class RoomMemberListResponse(BaseModel):
    """Paginated list of room members."""
    items: List[RoomMemberResponse]
    total: int


class RoomMessageResponse(BaseModel):
    """Response body representing a single RoomMessage entity."""
    id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    client_msg_id: uuid.UUID
    text: str
    created_at: datetime
    sender_username: Optional[str] = None

    model_config = {"from_attributes": True}


class RoomMessageListResponse(BaseModel):
    """Paginated list of room chat messages."""
    items: List[RoomMessageResponse]
    total: int

