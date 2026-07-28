"""
SQLAlchemy ORM Model for Blog entity and BlogStatus enumeration.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.comment import Comment


class BlogStatus(str, enum.Enum):
    """
    Enumeration for blog approval workflow statuses.
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Blog(Base):
    """
    Represents a blog post created by a writer or admin.
    """
    __tablename__ = "blogs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[BlogStatus] = mapped_column(
        SQLEnum(BlogStatus, name="blog_status", native_enum=False),
        default=BlogStatus.PENDING,
        nullable=False,
        index=True,
    )

    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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

    # Relationship to User
    author: Mapped["User"] = relationship(
        back_populates="blogs",
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="blog",
        cascade="all, delete-orphan",
    )
