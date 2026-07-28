"""
Repository Layer for Follow database operations.

Encapsulates all database CRUD queries for the Follow model using SQLAlchemy 2.0 async syntax.
Decouples database access logic from the Service and API layers.
Includes error handling for database constraint violations and connection failures.
"""

import logging
import uuid
from typing import List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow

logger = logging.getLogger(__name__)


class FollowRepository:
    """
    Data Access Object (DAO) for Follow entity.
    """

    async def get_by_pair(
        self, db: AsyncSession, follower_id: uuid.UUID, target_id: uuid.UUID
    ) -> Optional[Follow]:
        """
        Fetch a follow relationship record by exact follower and target UUIDs.
        """
        try:
            stmt = select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.target_id == target_id,
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching follow pair ({follower_id} -> {target_id}): {e}")
            raise

    async def create(
        self, db: AsyncSession, follower_id: uuid.UUID, target_id: uuid.UUID
    ) -> Follow:
        """
        Create and persist a new Follow relationship record.
        """
        db_follow = Follow(follower_id=follower_id, target_id=target_id)
        try:
            db.add(db_follow)
            await db.commit()
            await db.refresh(db_follow)
            return db_follow
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Integrity constraint violation creating follow: {e}")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating follow: {e}")
            raise

    async def delete(
        self, db: AsyncSession, follower_id: uuid.UUID, target_id: uuid.UUID
    ) -> bool:
        """
        Delete an existing follow relationship record.
        Returns True if a row was deleted, False if no matching relationship existed.
        """
        follow = await self.get_by_pair(db, follower_id=follower_id, target_id=target_id)
        if not follow:
            return False
        try:
            await db.delete(follow)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting follow: {e}")
            raise

    async def count_between_pair(
        self, db: AsyncSession, user_a_id: uuid.UUID, user_b_id: uuid.UUID
    ) -> int:
        """
        Count active directed follows between two users in EITHER direction (A -> B OR B -> A).
        Used by ConversationPolicy and WebSockets for direct messaging authorization.
        """
        try:
            stmt = select(func.count(Follow.id)).where(
                or_(
                    and_(Follow.follower_id == user_a_id, Follow.target_id == user_b_id),
                    and_(Follow.follower_id == user_b_id, Follow.target_id == user_a_id),
                )
            )
            result = await db.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Database error counting follows between {user_a_id} and {user_b_id}: {e}")
            raise

    async def get_following_user_ids(
        self, db: AsyncSession, follower_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[uuid.UUID]:
        """
        Fetch paginated list of target user IDs followed by follower_id.
        """
        try:
            stmt = (
                select(Follow.target_id)
                .where(Follow.follower_id == follower_id)
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching following IDs for {follower_id}: {e}")
            raise

    async def get_follower_user_ids(
        self, db: AsyncSession, target_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> List[uuid.UUID]:
        """
        Fetch paginated list of follower user IDs following target_id.
        """
        try:
            stmt = (
                select(Follow.follower_id)
                .where(Follow.target_id == target_id)
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching follower IDs for {target_id}: {e}")
            raise


# Singleton repository export
follow_repository = FollowRepository()
