"""
Pydantic v2 Schemas and Enumerations for Notification Event Taxonomy,
Navigation Targets, Safe Payloads, and Idempotency Rules.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class NotificationTypeEnum(str, enum.Enum):
    """
    Enumeration of versioned notification event types.
    """
    NEW_FOLLOWER = "new_follower"
    NEW_DIRECT_MESSAGE = "new_direct_message"
    BLOG_APPROVED = "blog_approved"
    BLOG_REJECTED = "blog_rejected"
    ROOM_REQUEST_APPROVED = "room_request_approved"
    ROOM_REQUEST_REJECTED = "room_request_rejected"
    ROLE_CHANGED = "role_changed"
    PERMISSION_OVERRIDE_CHANGED = "permission_override_changed"


class NavigationTargetEnum(str, enum.Enum):
    """
    Enumeration of valid frontend navigation target views.
    """
    PROFILE = "profile"
    DM_CONVERSATION = "dm_conversation"
    BLOG_DETAIL = "blog_detail"
    ROOM_DETAIL = "room_detail"
    ROOM_LIST = "room_list"
    ADMIN_PERMISSIONS = "admin_permissions"


class NotificationPayloadSchema(BaseModel):
    """
    Safe, non-sensitive payload schema for notification items.
    Explicitly forbids extra un-sanitized data fields.
    """
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    actor_id: uuid.UUID
    actor_username: str = Field(..., max_length=100)
    target_type: str = Field(..., max_length=50)
    target_id: uuid.UUID
    title: Optional[str] = Field(None, max_length=150)
    summary_text: Optional[str] = Field(None, max_length=255)
    navigation_target: NavigationTargetEnum
    navigation_params: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """
    Response schema for a single notification item.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    event_type: str
    payload: Dict[str, Any]
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    """
    Paginated list response for notifications.
    """
    items: List[NotificationResponse]
    total: int
    page: int
    size: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """
    Unread count scalar response.
    """
    unread_count: int


def should_suppress_actor_recipient(actor_id: uuid.UUID, recipient_id: uuid.UUID) -> bool:
    """
    Returns True if actor and recipient are the same user (self-notification).
    """
    return actor_id == recipient_id


def build_idempotency_key(
    event_type: NotificationTypeEnum,
    actor_id: uuid.UUID,
    recipient_id: uuid.UUID,
    target_id: uuid.UUID,
) -> str:
    """
    Constructs a deterministic deduplication key for notification persistence.
    Format: {event_type}:{actor_id}:{recipient_id}:{target_id}
    """
    return f"{event_type.value}:{actor_id}:{recipient_id}:{target_id}"

