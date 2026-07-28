"""
Pydantic schemas for the social follow feature.

Authorization matrix reference:
  .agents/artifacts/realtime-chat/authorization_matrix.md

Permitted follow pairs  (role of follower → role of target):
  user   → user   ✅
  user   → writer ✅
  writer → user   ✅
  writer → writer ✅
  admin  → any    ❌  (admins excluded from follows and DMs)
  any    → admin  ❌
  self   → self   ❌
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRole


class FollowCreate(BaseModel):
    """Request body for POST /api/v1/follows."""
    target_user_id: uuid.UUID = Field(
        description="UUID of the user or writer account to follow.",
    )


class FollowResponse(BaseModel):
    """
    Response body representing a single directed follow record.
    Returned on successful follow creation.
    """
    id: uuid.UUID
    follower_id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowableUserResponse(BaseModel):
    """
    Safe public summary of a user or writer account for discovery endpoints.

    INTENTIONALLY omits: email, hashed_password, stripe_customer_id,
    is_active, is_verified, updated_at.
    Only the minimum fields needed for social discovery are exposed.
    """
    id: uuid.UUID
    username: str
    role: UserRole
    is_following: bool = Field(
        description="True if the requesting user already follows this account.",
    )

    model_config = {"from_attributes": True}


class FollowerListResponse(BaseModel):
    """Paginated list of followable user summaries."""
    items: list[FollowableUserResponse]
    total: int
    page: int = 1
    page_size: int = 20
