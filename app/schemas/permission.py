"""
Pydantic v2 Schemas for Capabilities, User Permission Overrides, and Audit Logs.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.permission import CapabilityEnum, OverrideEffectEnum


class CapabilityStatusResponse(BaseModel):
    """
    Status of a single capability for a target user.
    """
    model_config = ConfigDict(from_attributes=True)

    capability: CapabilityEnum
    role_default: bool
    override: Optional[OverrideEffectEnum] = None
    effective_permission: bool


class UserCapabilitiesResponse(BaseModel):
    """
    List of all capability statuses for a given user.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    capabilities: List[CapabilityStatusResponse]


class UserOverrideUpdateRequest(BaseModel):
    """
    Payload for an admin setting or clearing a capability override on a user.
    """
    capability: CapabilityEnum
    effect: OverrideEffectEnum
    reason: Optional[str] = Field(None, max_length=255)


class PermissionAuditLogResponse(BaseModel):
    """
    Audit log entry detail for permission modifications.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    target_id: uuid.UUID
    capability: str
    previous_state: Optional[str]
    new_state: str
    reason: Optional[str]
    created_at: datetime
