"""
SQLAlchemy ORM Model for Direct Message.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import WS_MAX_TEXT_LEN
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User


class Message(Base):
    """
    Represents a direct message stored within a conversation.
    """
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
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

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    sender: Mapped["User"] = relationship(
        "User",
    )

    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
    )
