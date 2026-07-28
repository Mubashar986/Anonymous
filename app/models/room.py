"""
SQLAlchemy ORM Models for Community Rooms, Requests, Memberships, and Messages.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.core.constants import WS_MAX_TEXT_LEN

if TYPE_CHECKING:
    from app.models.user import User


class RoomRequestStatus(str, enum.Enum):
    """Workflow statuses for room requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RoomRequest(Base):
    """
    Tracks proposals for community room creation submitted by non-admin users.
    """
    __tablename__ = "room_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    status: Mapped[RoomRequestStatus] = mapped_column(
        SQLEnum(RoomRequestStatus, name="room_request_status", native_enum=False),
        default=RoomRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    decision_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # ORM relationships
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
    )
    decision_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[decision_by_id],
    )


class Room(Base):
    """
    Represents a multi-user public or private community chat room.
    """
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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

    # ORM relationships
    members: Mapped[List["RoomMember"]] = relationship(
        "RoomMember",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["RoomMessage"]] = relationship(
        "RoomMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )


class RoomMember(Base):
    """
    Tracks membership status, join times, and admin removals in community rooms.
    """
    __tablename__ = "room_members"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    removed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    removed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ORM relationships
    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    removed_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[removed_by_id],
    )

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
    )


class RoomMessage(Base):
    """
    Represents a persistent direct text message sent inside a community room.
    """
    __tablename__ = "room_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_msg_id: Mapped[uuid.UUID] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(
        String(WS_MAX_TEXT_LEN),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ORM relationships
    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="messages",
    )
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
    )

    __table_args__ = (
        Index("ix_room_messages_room_created", "room_id", "created_at"),
    )
