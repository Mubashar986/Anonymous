"""
Service Layer for Blog business logic, approval workflow, and role-based access control.
"""

import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_active_subscription
from app.models.blog import Blog, BlogStatus
from app.models.user import User, UserRole
from app.repositories import blog_repository
from app.schemas.blog import BlogApprove, BlogCreate, BlogUpdate
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum

logger = logging.getLogger(__name__)


class BlogService:
    """
    Business Logic Service for Blog management and permission enforcement.
    """

    async def create_blog(
        self, db: AsyncSession, current_user: User, blog_in: BlogCreate
    ) -> Blog:
        """
        Create a new blog.
        - Writers: Default status is PENDING (requires admin approval).
        - Admins: Default status is APPROVED immediately.
        """
        initial_status = (
            BlogStatus.APPROVED
            if current_user.role == UserRole.ADMIN
            else BlogStatus.PENDING
        )
        return await blog_repository.create(
            db=db,
            blog_in=blog_in,
            author_id=current_user.id,
            status=initial_status,
        )

    async def list_blogs(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """
        List blogs according to role-based visibility matrix:
        - Admin: Views ALL blogs (pending, approved, rejected).
        - Writer: Views all APPROVED blogs + their own blogs (regardless of status).
        - User: Views ONLY APPROVED blogs. Users must never see pending/rejected blogs.
        """
        if current_user.role == UserRole.ADMIN:
            return await blog_repository.get_all(db=db, skip=skip, limit=limit)
        elif current_user.role == UserRole.WRITER:
            return await blog_repository.get_visible_for_writer(
                db=db, writer_id=current_user.id, skip=skip, limit=limit
            )
        else:
            # Standard User: Only approved blogs
            return await blog_repository.get_by_status(
                db=db, status=BlogStatus.APPROVED, skip=skip, limit=limit
            )

    async def list_all_blogs_admin(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Blog]:
        """
        Admin-only endpoint to list all blogs.
        """
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view all blogs.",
            )
        return await blog_repository.get_all(db=db, skip=skip, limit=limit)

    async def get_blog_by_id(
        self, db: AsyncSession, current_user: User, blog_id: uuid.UUID
    ) -> Blog:
        """
        Fetch blog by ID, enforcing role-based visibility rules.
        """
        blog = await blog_repository.get_by_id(db=db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",
            )

        # Enforce visibility rules:
        # User: can only see if status == APPROVED
        if current_user.role == UserRole.USER and blog.status != BlogStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",  # Prevent disclosing pending blogs
            )

        # Writer: can see if status == APPROVED or if they are the author
        if (
            current_user.role == UserRole.WRITER
            and blog.status != BlogStatus.APPROVED
            and blog.author_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",
            )

        # Paywall check for premium blogs
        if blog.is_premium:
            await require_active_subscription(current_user=current_user, db=db)

        return blog

    async def update_blog(
        self, db: AsyncSession, current_user: User, blog_id: uuid.UUID, blog_in: BlogUpdate
    ) -> Blog:
        """
        Update blog post:
        - Admin: Can update any blog.
        - Writer: Can update only their own blog.
        - User: Cannot update blogs (blocked by route dependency).
        """
        blog = await blog_repository.get_by_id(db=db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",
            )

        # Check ownership unless Admin
        if current_user.role != UserRole.ADMIN and blog.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own blogs.",
            )

        return await blog_repository.update(db=db, db_blog=blog, blog_in=blog_in)

    async def delete_blog(
        self, db: AsyncSession, current_user: User, blog_id: uuid.UUID
    ) -> None:
        """
        Delete blog post:
        - Admin: Can delete any blog.
        - Writer: Can delete only their own blog.
        - User: Cannot delete blogs (blocked by route dependency).
        """
        blog = await blog_repository.get_by_id(db=db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",
            )

        # Check ownership unless Admin
        if current_user.role != UserRole.ADMIN and blog.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own blogs.",
            )

        await blog_repository.delete(db=db, db_blog=blog)

    async def approve_blog(
        self, db: AsyncSession, current_user: User, blog_id: uuid.UUID, approve_in: BlogApprove
    ) -> Blog:
        """
        Approve or Reject blog post (Admin only).
        """
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to approve or reject blogs.",
            )

        blog = await blog_repository.get_by_id(db=db, blog_id=blog_id)
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found.",
            )

        updated_blog = await blog_repository.update_status(
            db=db, db_blog=blog, status=approve_in.status
        )

        event_type = (
            NotificationTypeEnum.BLOG_APPROVED
            if approve_in.status == BlogStatus.APPROVED
            else NotificationTypeEnum.BLOG_REJECTED
        )
        status_text = "approved" if approve_in.status == BlogStatus.APPROVED else "rejected"

        await notification_service.create_notification_event(
            db=db,
            recipient_id=updated_blog.author_id,
            actor_id=current_user.id,
            actor_username=current_user.username,
            event_type=event_type,
            target_type="blog",
            target_id=updated_blog.id,
            title=f"Blog Post {status_text.capitalize()}",
            summary_text=f"Your blog post '{updated_blog.title}' was {status_text}.",
            navigation_target=NavigationTargetEnum.BLOG_DETAIL,
            navigation_params={"blog_id": str(updated_blog.id)},
        )

        return updated_blog


# Singleton service instance
blog_service = BlogService()
