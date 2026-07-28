"""
SQLAlchemy ORM Model for Comment entity.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.blog import Blog
    from app.models.user import User


class Comment(Base):
    """
    Represents a comment left on a blog post.
    """
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    blog_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("blogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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

    # Relationships
    blog: Mapped["Blog"] = relationship(
        back_populates="comments",
    )

    author: Mapped["User"] = relationship(
        back_populates="comments",
    )
