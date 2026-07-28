"""
Service Layer for Comment business logic and permission enforcement.
"""

import logging
import uuid
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import BlogStatus
from app.models.comment import Comment
from app.models.user import User, UserRole
from app.repositories import blog_repository, comment_repository
from app.schemas.comment import CommentCreate, CommentUpdate

logger = logging.getLogger(__name__)


class CommentService:
    """
    Business Logic Service for Comment creation, retrieval, updates, and deletion.
    """

    async def create_comment(
        self,
        db: AsyncSession,
        current_user: User,
        blog_id: uuid.UUID,
        comment_in: CommentCreate,
    ) -> Comment:
        """
        Create a comment on a blog post:
        - Blog must exist.
        - Blog must be APPROVED (unless current_user is blog author or ADMIN).
        """
        blog = await blog_repository.get_by_id(db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target blog post not found.",
            )

        # Users & Writers can only comment on APPROVED blogs (or their own blog if author)
        if (
            current_user.role != UserRole.ADMIN
            and blog.author_id != current_user.id
            and blog.status != BlogStatus.APPROVED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comments can only be added to approved blog posts.",
            )

        return await comment_repository.create(
            db=db,
            comment_in=comment_in,
            blog_id=blog_id,
            author_id=current_user.id,
        )

    async def get_comments_for_blog(
        self,
        db: AsyncSession,
        current_user: User,
        blog_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Comment]:
        """
        Fetch comments on a blog post if the blog is visible to the current user's role.
        """
        blog = await blog_repository.get_by_id(db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target blog post not found.",
            )

        # Check blog visibility
        if (
            current_user.role == UserRole.USER
            and blog.status != BlogStatus.APPROVED
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target blog post not found.",
            )

        if (
            current_user.role == UserRole.WRITER
            and blog.status != BlogStatus.APPROVED
            and blog.author_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target blog post not found.",
            )

        return await comment_repository.get_by_blog_id(
            db=db, blog_id=blog_id, skip=skip, limit=limit
        )

    async def get_all_comments_admin(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """
        Admin-only endpoint to view all comments across all writer blogs.
        """
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view all comments.",
            )
        return await comment_repository.get_all(db=db, skip=skip, limit=limit)

    async def update_comment(
        self,
        db: AsyncSession,
        current_user: User,
        comment_id: uuid.UUID,
        comment_in: CommentUpdate,
    ) -> Comment:
        """
        Update a comment:
        - Admin: Can update any comment.
        - Users/Writers: Can only update their own comments.
        """
        comment = await comment_repository.get_by_id(db, comment_id=comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        if current_user.role != UserRole.ADMIN and comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own comments.",
            )

        return await comment_repository.update(db=db, db_comment=comment, comment_in=comment_in)

    async def delete_comment(
        self, db: AsyncSession, current_user: User, comment_id: uuid.UUID
    ) -> None:
        """
        Delete a comment:
        - Admin: Can delete any comment.
        - Users/Writers: Can only delete their own comments.
        """
        comment = await comment_repository.get_by_id(db, comment_id=comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        if current_user.role != UserRole.ADMIN and comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments.",
            )

        await comment_repository.delete(db=db, db_comment=comment)


# Singleton service instance
comment_service = CommentService()
