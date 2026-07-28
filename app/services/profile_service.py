import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists

from app.models.user import User, UserRole
from app.models.follow import Follow
from app.models.blog import Blog, BlogStatus
from app.schemas.user import UserProfileResponse
from app.repositories.user_repository import user_repository
from app.repositories.follow_repository import follow_repository

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Service layer to manage user profile aggregates and privacy filters.
    """

    async def get_user_profile(
        self, db: AsyncSession, target_id: uuid.UUID, viewer_id: uuid.UUID, skip: int = 0, limit: int = 10
    ) -> UserProfileResponse:
        """
        Retrieves public profile details for target_id.
        Enforces privacy constraints for inactive users and admin accounts.
        """
        # Define aggregate scalar subqueries
        followers_sub = select(func.count(Follow.id)).where(Follow.target_id == target_id).scalar_subquery()
        following_sub = select(func.count(Follow.id)).where(Follow.follower_id == target_id).scalar_subquery()
        is_following_sub = exists().where(
            Follow.follower_id == viewer_id,
            Follow.target_id == target_id
        ).select().scalar_subquery()



        # Fetch target user + aggregates in a single roundtrip
        stmt = select(User, followers_sub, following_sub, is_following_sub).where(User.id == target_id)
        result = await db.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )

        target_user, followers_count, following_count, is_following = row

        # Privacy rules: Inactive users and Administrators are invisible on the social graph
        if not target_user.is_active or target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )

        # Fetch writer approved blogs if the target has writer privileges (paginated)
        articles = None
        if target_user.role == UserRole.WRITER:
            articles_stmt = (
                select(Blog)
                .where(Blog.author_id == target_id, Blog.status == BlogStatus.APPROVED)
                .order_by(Blog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            articles_res = await db.execute(articles_stmt)
            db_articles = articles_res.scalars().all()
            
            articles = [
                {
                    "id": art.id,
                    "title": art.title,
                    "content": art.content,
                    "is_premium": art.is_premium,
                    "status": art.status.value if hasattr(art.status, 'value') else art.status,
                    "author_id": art.author_id,
                    "created_at": art.created_at,
                    "updated_at": art.updated_at,
                }
                for art in db_articles
            ]

        return UserProfileResponse(
            id=target_user.id,
            username=target_user.username,
            role=target_user.role,
            created_at=target_user.created_at,
            bio=target_user.bio,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
            articles=articles,
        )


profile_service = ProfileService()
