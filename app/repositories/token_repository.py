"""
Repository Layer for RefreshToken database operations.

Encapsulates database operations for session tracking, token validation, and token revocation.
Includes error handling for database constraint violations and connection failures.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.token import RefreshToken

logger = logging.getLogger(__name__)


class TokenRepository:
    """
    Data Access Object (DAO) for RefreshToken entity.
    """

    async def create(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """
        Persist a new refresh token session in the database.
        """
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=False,
        )
        try:
            db.add(db_token)
            await db.commit()
            await db.refresh(db_token)
            return db_token
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Integrity constraint violation creating token: {e}")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating refresh token: {e}")
            raise

    async def get_by_token(self, db: AsyncSession, token: str) -> Optional[RefreshToken]:
        """
        Find a refresh token by its token string.
        """
        try:
            result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching refresh token: {e}")
            raise

    async def revoke(self, db: AsyncSession, db_token: RefreshToken) -> RefreshToken:
        """
        Revoke a specific refresh token (soft delete).
        """
        db_token.is_revoked = True
        try:
            db.add(db_token)
            await db.commit()
            await db.refresh(db_token)
            return db_token
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error revoking token: {e}")
            raise

    async def revoke_all_for_user(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """
        Revoke all active refresh tokens for a user (e.g. on security reset or logout from all devices).
        """
        try:
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
                .values(is_revoked=True)
            )
            await db.execute(stmt)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error revoking all tokens for user {user_id}: {e}")
            raise


# Instantiate singleton repository
token_repository = TokenRepository()
