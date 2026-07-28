"""
Repository Layer for Blog database operations.

Encapsulates all database CRUD queries for the Blog entity using SQLAlchemy 2.0 async syntax.
"""

import logging
import uuid
from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import Blog, BlogStatus
from app.schemas.blog import BlogCreate, BlogUpdate

logger = logging.getLogger(__name__)


class BlogRepository:
    """
    Data Access Object (DAO) for Blog entity.
    """

    async def get_by_id(self, db: AsyncSession, blog_id: uuid.UUID) -> Optional[Blog]:
        """
        Fetch a blog by primary key ID.
        """
        try:
            result = await db.execute(select(Blog).where(Blog.id == blog_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching blog {blog_id}: {e}")
            raise

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Blog]:
        """
        Fetch all blogs regardless of status (Admin view).
        """
        try:
            result = await db.execute(
                select(Blog).order_by(Blog.created_at.desc()).offset(skip).limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching all blogs: {e}")
            raise

    async def get_by_status(
        self, db: AsyncSession, status: BlogStatus, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """
        Fetch blogs by specific approval status (e.g. APPROVED for Users).
        """
        try:
            result = await db.execute(
                select(Blog)
                .where(Blog.status == status)
                .order_by(Blog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching blogs with status {status}: {e}")
            raise

    async def get_visible_for_writer(
        self, db: AsyncSession, writer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """
        Fetch blogs visible to a writer (all APPROVED blogs + writer's own blogs).
        """
        try:
            result = await db.execute(
                select(Blog)
                .where(
                    or_(
                        Blog.status == BlogStatus.APPROVED,
                        Blog.author_id == writer_id,
                    )
                )
                .order_by(Blog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching visible blogs for writer {writer_id}: {e}")
            raise

    async def get_by_author(
        self, db: AsyncSession, author_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """
        Fetch blogs created by a specific author.
        """
        try:
            result = await db.execute(
                select(Blog)
                .where(Blog.author_id == author_id)
                .order_by(Blog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching blogs by author {author_id}: {e}")
            raise

    async def create(
        self,
        db: AsyncSession,
        blog_in: BlogCreate,
        author_id: uuid.UUID,
        status: BlogStatus = BlogStatus.PENDING,
    ) -> Blog:
        """
        Create a new blog record in the database.
        """
        db_blog = Blog(
            title=blog_in.title,
            content=blog_in.content,
            is_premium=blog_in.is_premium,
            status=status,
            author_id=author_id,
        )
        try:
            db.add(db_blog)
            await db.commit()
            await db.refresh(db_blog)
            return db_blog
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating blog: {e}")
            raise

    async def update(self, db: AsyncSession, db_blog: Blog, blog_in: BlogUpdate) -> Blog:
        """
        Update an existing blog post.
        """
        update_data = blog_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_blog, field, value)

        try:
            db.add(db_blog)
            await db.commit()
            await db.refresh(db_blog)
            return db_blog
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating blog {db_blog.id}: {e}")
            raise

    async def update_status(self, db: AsyncSession, db_blog: Blog, status: BlogStatus) -> Blog:
        """
        Update the approval status of a blog post.
        """
        db_blog.status = status
        try:
            db.add(db_blog)
            await db.commit()
            await db.refresh(db_blog)
            return db_blog
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating blog status {db_blog.id}: {e}")
            raise

    async def delete(self, db: AsyncSession, db_blog: Blog) -> None:
        """
        Delete a blog post from the database.
        """
        try:
            await db.delete(db_blog)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting blog {db_blog.id}: {e}")
            raise


# Singleton repository instance
blog_repository = BlogRepository()
