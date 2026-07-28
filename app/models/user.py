"""
SQLAlchemy ORM Model for User.

Defines the database schema, validations, and relationships for application users.
Uses modern SQLAlchemy 2.0 Mapped type annotations.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

# Avoid circular imports at runtime for type checking
if TYPE_CHECKING:
    from app.models.token import RefreshToken
    from app.models.blog import Blog
    from app.models.comment import Comment
    from app.models.subscription import Subscription
    from app.models.follow import Follow


class UserRole(str, enum.Enum):
    """
    Enumeration of application user roles for RBAC.
    """
    ADMIN = "admin"
    WRITER = "writer"
    USER = "user"


class User(Base):
    """
    Represents a user account in the system.
    """
    __tablename__ = "users"

    # UUIDs prevent id enumeration/scraping attacks
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    
    # User status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
    )

    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
    
    # Time stamps
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
    # Cascade deletes all associated refresh tokens if user is deleted
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    blogs: Mapped[List["Blog"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

    subscription: Mapped[Optional["Subscription"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    following_associations: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="[Follow.follower_id]",
        back_populates="follower",
        cascade="all, delete-orphan",
    )

    follower_associations: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="[Follow.target_id]",
        back_populates="target",
        cascade="all, delete-orphan",
    )
