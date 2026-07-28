"""
Repository Layer for User database operations.

Encapsulates all database CRUD queries for the User model using SQLAlchemy 2.0 async syntax.
Decouples database access logic from the Service and API layers.
Includes error handling for database constraint violations and connection failures.
"""

import logging
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Data Access Object (DAO) for User entity.
    """

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch a user by their UUID primary key.
        """
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by id {user_id}: {e}")
            raise

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Fetch a user by their unique email address.
        """
        try:
            result = await db.execute(select(User).where(User.email == email.lower()))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by email: {e}")
            raise

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Fetch a user by their unique username.
        """
        try:
            result = await db.execute(select(User).where(User.username == username.lower()))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by username: {e}")
            raise

    async def create(self, db: AsyncSession, user_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user record in the database.
        Always defaults role to UserRole.USER to prevent signup privilege escalation.
        """
        db_user = User(
            email=user_in.email.lower(),
            username=user_in.username.lower(),
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
        )
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Integrity constraint violation creating user: {e}")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating user: {e}")
            raise

    async def update(self, db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
        """
        Update an existing user record.
        """
        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value:
                value = value.lower()
            if field == "username" and value:
                value = value.lower()
            setattr(db_user, field, value)
            
        try:
            db_user = await db.merge(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user

        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Integrity constraint violation updating user: {e}")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating user: {e}")
            raise

    async def update_role(self, db: AsyncSession, db_user: User, role: UserRole) -> User:
        """
        Update user role (Admin authorization required at Service/API layer).
        """
        db_user.role = role
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating user role: {e}")
            raise

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Fetch all user records from the database with pagination (Admin only).
        """
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching all users: {e}")
            raise

    async def toggle_verification(self, db: AsyncSession, db_user: User) -> User:
        """
        Toggle user account email verification status (Admin only).
        """
        db_user.is_verified = not db_user.is_verified
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error toggling user verification: {e}")
            raise

    async def update_stripe_customer_id(
        self, db: AsyncSession, db_user: User, stripe_customer_id: str
    ) -> User:
        """
        Update user's Stripe customer ID.
        """
        db_user.stripe_customer_id = stripe_customer_id
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating user stripe_customer_id: {e}")
            raise


# Instantiate singleton repository
user_repository = UserRepository()
