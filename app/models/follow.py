"""
SQLAlchemy ORM Model for Follow relationships.

Represents directed social follow links between user accounts.
Uses modern SQLAlchemy 2.0 Mapped type annotations.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Follow(Base):
    """
    Represents a directed follow relationship from a follower user to a target user.
    """
    __tablename__ = "follows"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    follower_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ORM Relationships
    follower: Mapped["User"] = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="following_associations",
    )

    target: Mapped["User"] = relationship(
        "User",
        foreign_keys=[target_id],
        back_populates="follower_associations",
    )

    __table_args__ = (
        CheckConstraint("follower_id != target_id", name="ck_follows_no_self_follow"),
        UniqueConstraint("follower_id", "target_id", name="uq_follows_follower_target"),
    )
