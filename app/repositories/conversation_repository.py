"""
Repository Layer for Conversation database operations.
"""

import logging
import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationParticipant

logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Data Access Object (DAO) for Conversation and ConversationParticipant entities.
    """

    async def get_by_id(
        self, db: AsyncSession, conversation_id: uuid.UUID
    ) -> Optional[Conversation]:
        """
        Fetch conversation by primary key with participants loaded.
        """
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(
                    selectinload(Conversation.participants).selectinload(
                        ConversationParticipant.user
                    )
                )
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching conversation {conversation_id}: {e}")
            raise

    async def get_by_participant_pair(
        self, db: AsyncSession, user_a_id: uuid.UUID, user_b_id: uuid.UUID
    ) -> Optional[Conversation]:
        """
        Fetch conversation containing BOTH user_a_id and user_b_id regardless of ordering.
        """
        try:
            stmt = (
                select(ConversationParticipant.conversation_id)
                .where(ConversationParticipant.user_id.in_([user_a_id, user_b_id]))
                .group_by(ConversationParticipant.conversation_id)
                .having(func.count(ConversationParticipant.user_id) == 2)
            )
            res = await db.execute(stmt)
            conv_id = res.scalar_one_or_none()
            if not conv_id:
                return None
            return await self.get_by_id(db, conversation_id=conv_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching conversation pair ({user_a_id}, {user_b_id}): {e}")
            raise

    async def get_or_create_for_pair(
        self, db: AsyncSession, user_a_id: uuid.UUID, user_b_id: uuid.UUID
    ) -> Conversation:
        """
        Fetch existing conversation or create a new 1-to-1 conversation for pair.
        """
        existing = await self.get_by_participant_pair(db, user_a_id, user_b_id)
        if existing:
            return existing

        try:
            conv = Conversation()
            db.add(conv)
            await db.flush()

            p1 = ConversationParticipant(conversation_id=conv.id, user_id=user_a_id)
            p2 = ConversationParticipant(conversation_id=conv.id, user_id=user_b_id)
            db.add_all([p1, p2])
            await db.commit()
            return await self.get_by_id(db, conversation_id=conv.id)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating conversation for pair ({user_a_id}, {user_b_id}): {e}")
            raise

    async def is_participant(
        self, db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """
        Check if user_id is a participant in conversation_id.
        """
        try:
            stmt = select(func.count(ConversationParticipant.id)).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            res = await db.execute(stmt)
            return (res.scalar() or 0) > 0
        except SQLAlchemyError as e:
            logger.error(f"Database error checking participant ({user_id} in {conversation_id}): {e}")
            raise

    async def get_user_conversations(
        self, db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[Conversation]:
        """
        Fetch paginated list of conversations user_id belongs to.
        """
        try:
            stmt = (
                select(Conversation)
                .join(ConversationParticipant)
                .where(ConversationParticipant.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .offset(skip)
                .limit(limit)
                .options(
                    selectinload(Conversation.participants).selectinload(
                        ConversationParticipant.user
                    )
                )
            )
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching conversations for user {user_id}: {e}")
            raise


conversation_repository = ConversationRepository()
