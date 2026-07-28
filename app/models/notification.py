"""
SQLAlchemy ORM Model for Persisted Notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """
    Represents a persisted in-app notification record belonging to a recipient user.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
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

    # Relationships
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        lazy="selectin",
    )
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[actor_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_notifications_recipient_created", "recipient_id", "created_at"),
        Index("idx_notifications_recipient_unread", "recipient_id", "is_read"),
        Index("uix_notifications_idempotency", "idempotency_key", unique=True),
    )
