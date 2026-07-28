"""
Service Layer for Follow relationship business policy & authorization.

Enforces the authorization matrix defined in .agents/artifacts/realtime-chat/authorization_matrix.md:
  - User <-> User follows allowed
  - User <-> Writer follows allowed
  - Writer <-> Writer follows allowed
  - Self-follows forbidden (HTTP 400)
  - Admin follows forbidden (HTTP 403)
  - Target account must exist and be active (HTTP 404 / 400)
"""

import logging
import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.user import User, UserRole
from app.repositories.follow_repository import follow_repository
from app.repositories.user_repository import user_repository
from app.schemas.follow import FollowableUserResponse, FollowerListResponse
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum

logger = logging.getLogger(__name__)


class FollowService:
    """
    Business logic and authorization enforcement service for social follows.
    """

    async def follow_user(
        self, db: AsyncSession, current_user: User, target_user_id: uuid.UUID
    ) -> Follow:
        """
        Follow a target user account.
        Enforces role matrix, self-follow guard, and active user validation.
        """
        # 1. Self-follow check
        if current_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself.",
            )

        # 2. Actor role check (Admins cannot follow)
        if current_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrators cannot initiate social follows.",
            )

        # 3. Target user existence & active status check
        target_user = await user_repository.get_by_id(db, user_id=target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user account not found.",
            )

        if not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot follow an inactive user account.",
            )

        # 4. Target role check (Admins cannot be followed)
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot follow an administrator account.",
            )

        # 5. Duplicate check
        existing = await follow_repository.get_by_pair(
            db, follower_id=current_user.id, target_id=target_user_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already following this user.",
            )

        # Create follow relationship
        follow = await follow_repository.create(
            db, follower_id=current_user.id, target_id=target_user_id
        )
        logger.info(f"User {current_user.id} followed user {target_user_id}")

        # Emit notification to target user
        await notification_service.create_notification_event(
            db=db,
            recipient_id=target_user_id,
            actor_id=current_user.id,
            actor_username=current_user.username,
            event_type=NotificationTypeEnum.NEW_FOLLOWER,
            target_type="user",
            target_id=current_user.id,
            title="New Follower",
            summary_text=f"@{current_user.username} started following you.",
            navigation_target=NavigationTargetEnum.PROFILE,
            navigation_params={"user_id": str(current_user.id)},
        )

        return follow

    async def unfollow_user(
        self, db: AsyncSession, current_user: User, target_user_id: uuid.UUID
    ) -> bool:
        """
        Unfollow a target user account.
        """
        deleted = await follow_repository.delete(
            db, follower_id=current_user.id, target_id=target_user_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Follow relationship does not exist.",
            )
        logger.info(f"User {current_user.id} unfollowed user {target_user_id}")
        return True

    async def can_send_dm(
        self, db: AsyncSession, user_a_id: uuid.UUID, user_b_id: uuid.UUID
    ) -> bool:
        """
        Check if direct messaging is authorized between user_a and user_b.
        Returns True if at least one directed follow exists between the pair and neither is an Admin.
        """
        user_a = await user_repository.get_by_id(db, user_id=user_a_id)
        user_b = await user_repository.get_by_id(db, user_id=user_b_id)

        if not user_a or not user_b:
            return False

        # Admins excluded from direct chat
        if user_a.role == UserRole.ADMIN or user_b.role == UserRole.ADMIN:
            return False

        count = await follow_repository.count_between_pair(db, user_a_id, user_b_id)
        return count > 0

    async def get_following(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 20
    ) -> FollowerListResponse:
        """Fetch paginated list of accounts followed by current_user."""
        target_ids = await follow_repository.get_following_user_ids(
            db, follower_id=current_user.id, skip=skip, limit=limit
        )
        if not target_ids:
            return FollowerListResponse(items=[], total=0, page=(skip // limit) + 1, page_size=limit)

        # Bulk fetch target users
        stmt = select(User).where(User.id.in_(target_ids), User.is_active == True)
        res = await db.execute(stmt)
        users = res.scalars().all()

        user_map = {u.id: u for u in users}
        items = []
        for target_id in target_ids:
            u = user_map.get(target_id)
            if u:
                items.append(
                    FollowableUserResponse(
                        id=u.id, username=u.username, role=u.role, is_following=True
                    )
                )
        return FollowerListResponse(items=items, total=len(items), page=(skip // limit) + 1, page_size=limit)

    async def get_followers(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 20
    ) -> FollowerListResponse:
        """Fetch paginated list of accounts following current_user."""
        follower_ids = await follow_repository.get_follower_user_ids(
            db, target_id=current_user.id, skip=skip, limit=limit
        )
        if not follower_ids:
            return FollowerListResponse(items=[], total=0, page=(skip // limit) + 1, page_size=limit)

        # 1. Bulk fetch follower users
        stmt = select(User).where(User.id.in_(follower_ids), User.is_active == True)
        res = await db.execute(stmt)
        users = res.scalars().all()
        user_map = {u.id: u for u in users}

        # 2. Bulk query follow relationships from current_user to these followers
        followed_stmt = select(Follow.target_id).where(
            Follow.follower_id == current_user.id,
            Follow.target_id.in_(follower_ids)
        )
        followed_res = await db.execute(followed_stmt)
        followed_set = set(followed_res.scalars().all())

        items = []
        for follower_id in follower_ids:
            u = user_map.get(follower_id)
            if u:
                items.append(
                    FollowableUserResponse(
                        id=u.id, username=u.username, role=u.role, is_following=(u.id in followed_set)
                    )
                )
        return FollowerListResponse(items=items, total=len(items), page=(skip // limit) + 1, page_size=limit)

    async def discover_users(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 20
    ) -> FollowerListResponse:
        """Fetch list of user & writer accounts eligible to follow, with is_following state."""
        all_users = await user_repository.get_all(db, skip=skip, limit=limit)
        
        target_ids = [
            u.id for u in all_users
            if u.id != current_user.id and u.role != UserRole.ADMIN and u.is_active
        ]
        
        if not target_ids:
            return FollowerListResponse(items=[], total=0, page=(skip // limit) + 1, page_size=limit)

        # Bulk check follows
        followed_stmt = select(Follow.target_id).where(
            Follow.follower_id == current_user.id,
            Follow.target_id.in_(target_ids)
        )
        followed_res = await db.execute(followed_stmt)
        followed_set = set(followed_res.scalars().all())

        items = []
        for u in all_users:
            if u.id == current_user.id or u.role == UserRole.ADMIN or not u.is_active:
                continue
            items.append(
                FollowableUserResponse(
                    id=u.id, username=u.username, role=u.role, is_following=(u.id in followed_set)
                )
            )
        return FollowerListResponse(items=items, total=len(items), page=(skip // limit) + 1, page_size=limit)


# Singleton service export
follow_service = FollowService()
