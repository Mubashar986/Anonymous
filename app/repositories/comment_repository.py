"""
Repository Layer for Comment database operations.

Encapsulates all database CRUD queries for the Comment entity using SQLAlchemy 2.0 async syntax.
"""

import logging
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate

logger = logging.getLogger(__name__)


class CommentRepository:
    """
    Data Access Object (DAO) for Comment entity.
    """

    async def get_by_id(self, db: AsyncSession, comment_id: uuid.UUID) -> Optional[Comment]:
        """
        Fetch a comment by primary key ID.
        """
        try:
            result = await db.execute(select(Comment).where(Comment.id == comment_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching comment {comment_id}: {e}")
            raise

    async def get_by_blog_id(
        self, db: AsyncSession, blog_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """
        Fetch all comments left on a specific blog post.
        """
        try:
            result = await db.execute(
                select(Comment)
                .where(Comment.blog_id == blog_id)
                .order_by(Comment.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching comments for blog {blog_id}: {e}")
            raise

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Comment]:
        """
        Fetch all comments across all blogs (Admin view).
        """
        try:
            result = await db.execute(
                select(Comment).order_by(Comment.created_at.desc()).offset(skip).limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching all comments: {e}")
            raise

    async def create(
        self,
        db: AsyncSession,
        comment_in: CommentCreate,
        blog_id: uuid.UUID,
        author_id: uuid.UUID,
    ) -> Comment:
        """
        Create a new comment record in the database.
        """
        db_comment = Comment(
            content=comment_in.content,
            blog_id=blog_id,
            author_id=author_id,
        )
        try:
            db.add(db_comment)
            await db.commit()
            await db.refresh(db_comment)
            return db_comment
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating comment: {e}")
            raise

    async def update(self, db: AsyncSession, db_comment: Comment, comment_in: CommentUpdate) -> Comment:
        """
        Update an existing comment record.
        """
        db_comment.content = comment_in.content
        try:
            db.add(db_comment)
            await db.commit()
            await db.refresh(db_comment)
            return db_comment
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating comment {db_comment.id}: {e}")
            raise

    async def delete(self, db: AsyncSession, db_comment: Comment) -> None:
        """
        Delete a comment record from the database.
        """
        try:
            await db.delete(db_comment)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting comment {db_comment.id}: {e}")
            raise


# Singleton repository instance
comment_repository = CommentRepository()
