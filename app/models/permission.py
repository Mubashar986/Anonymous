"""
SQLAlchemy ORM Models and Enumerations for Permissions & Policy Evaluation.

Defines CapabilityEnum, OverrideEffectEnum, UserPermissionOverride, and PermissionAuditLog.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class CapabilityEnum(str, enum.Enum):
    """
    Enumeration of versioned system capabilities.
    """
    CAN_FOLLOW = "can_follow"
    CAN_START_DIRECT_MESSAGE = "can_start_direct_message"
    CAN_SEND_DIRECT_MESSAGE = "can_send_direct_message"
    CAN_REQUEST_ROOM = "can_request_room"
    CAN_CREATE_ROOM = "can_create_room"
    CAN_SUBMIT_BLOG = "can_submit_blog"
    CAN_MARK_BLOG_PREMIUM = "can_mark_blog_premium"


class OverrideEffectEnum(str, enum.Enum):
    """
    Enumeration of user capability override states.
    """
    ALLOW = "allow"
    DENY = "deny"
    INHERIT = "inherit"


# Baseline capability defaults by user role
ROLE_DEFAULT_CAPABILITIES = {
    "user": {
        CapabilityEnum.CAN_FOLLOW: True,
        CapabilityEnum.CAN_START_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_SEND_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_REQUEST_ROOM: True,
        CapabilityEnum.CAN_CREATE_ROOM: False,
        CapabilityEnum.CAN_SUBMIT_BLOG: False,
        CapabilityEnum.CAN_MARK_BLOG_PREMIUM: False,
    },
    "writer": {
        CapabilityEnum.CAN_FOLLOW: True,
        CapabilityEnum.CAN_START_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_SEND_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_REQUEST_ROOM: True,
        CapabilityEnum.CAN_CREATE_ROOM: True,
        CapabilityEnum.CAN_SUBMIT_BLOG: True,
        CapabilityEnum.CAN_MARK_BLOG_PREMIUM: True,
    },
    "admin": {
        CapabilityEnum.CAN_FOLLOW: True,
        CapabilityEnum.CAN_START_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_SEND_DIRECT_MESSAGE: True,
        CapabilityEnum.CAN_REQUEST_ROOM: True,
        CapabilityEnum.CAN_CREATE_ROOM: True,
        CapabilityEnum.CAN_SUBMIT_BLOG: True,
        CapabilityEnum.CAN_MARK_BLOG_PREMIUM: True,
    },
}


class UserPermissionOverride(Base):
    """
    Represents a specific per-user capability override (ALLOW or DENY).
    """
    __tablename__ = "user_permission_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    capability: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    is_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("uix_user_capability", "user_id", "capability", unique=True),
    )


class PermissionAuditLog(Base):
    """
    Immutable audit log entry recording access control policy modifications.
    """
    __tablename__ = "permission_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    capability: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    previous_state: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    new_state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
