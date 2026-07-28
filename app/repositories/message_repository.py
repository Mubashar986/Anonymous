"""
Repository Layer for Message database operations.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message

logger = logging.getLogger(__name__)


class MessageRepository:
    """
    Data Access Object (DAO) for Message entity.
    """

    async def get_by_client_msg_id(
        self, db: AsyncSession, client_msg_id: uuid.UUID
    ) -> Optional[Message]:
        """
        Fetch message by unique client_msg_id idempotency key.
        """
        try:
            stmt = select(Message).where(Message.client_msg_id == client_msg_id)
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching message by client_msg_id {client_msg_id}: {e}")
            raise

    async def create(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        client_msg_id: uuid.UUID,
        text: str,
    ) -> Message:
        """
        Create and persist a new Message record with idempotency handling.
        """
        # 1. Idempotency check
        existing = await self.get_by_client_msg_id(db, client_msg_id=client_msg_id)
        if existing:
            return existing

        db_msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            client_msg_id=client_msg_id,
            text=text,
        )
        try:
            db.add(db_msg)
            await db.commit()
            await db.refresh(db_msg)
            return db_msg
        except IntegrityError as e:
            await db.rollback()
            # Duplicate client_msg_id hit race condition -> return existing
            existing = await self.get_by_client_msg_id(db, client_msg_id=client_msg_id)
            if existing:
                return existing
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating message: {e}")
            raise

    async def get_history(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        before_timestamp: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Message]:
        """
        Fetch cursor-paginated message history for a conversation.
        """
        try:
            stmt = select(Message).where(Message.conversation_id == conversation_id)
            if before_timestamp:
                stmt = stmt.where(Message.created_at < before_timestamp)
            stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
            res = await db.execute(stmt)
            messages = list(res.scalars().all())
            # Return ordered chronologically for rendering
            return list(reversed(messages))
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching message history for {conversation_id}: {e}")
            raise


message_repository = MessageRepository()
