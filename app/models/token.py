"""
SQLAlchemy ORM Model for RefreshToken.

Maintains a record of issued refresh tokens mapped to specific users,
enabling refresh token rotation, blacklisting, and revocation.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    """
    Represents a user's active session refresh token.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Store refresh token hashes (or the token string itself)
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        index=True,
        nullable=False,
    )
    
    # On user deletion, Cascade the removal of their tokens
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens",
    )
