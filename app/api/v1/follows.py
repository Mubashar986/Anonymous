"""
API Router for Social Follow Endpoints.

Handles follow creation, unfollow removal, and list queries for user accounts.
"""

import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies import get_current_active_user, require_capability
from app.models.permission import CapabilityEnum
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.follow import FollowCreate, FollowerListResponse, FollowResponse
from app.services.follow_service import follow_service

router = APIRouter(prefix="/follows", tags=["Follows"])


@router.post(
    "",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user account",
    description="Follow an active user or writer account. Admins and self-follows are forbidden.",
)
async def follow_user(
    follow_in: FollowCreate,
    current_user: User = Depends(require_capability(CapabilityEnum.CAN_FOLLOW)),
    db: AsyncSession = Depends(get_db),
) -> FollowResponse:

    return await follow_service.follow_user(
        db, current_user=current_user, target_user_id=follow_in.target_user_id
    )


@router.delete(
    "/{target_user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Unfollow a user account",
    description="Remove an existing follow relationship.",
)
async def unfollow_user(
    target_user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await follow_service.unfollow_user(
        db, current_user=current_user, target_user_id=target_user_id
    )
    return MessageResponse(message="Successfully unfollowed user.")


@router.get(
    "/following",
    response_model=FollowerListResponse,
    status_code=status.HTTP_200_OK,
    summary="List accounts current user follows",
    description="Fetch paginated list of accounts followed by the authenticated user.",
)
async def list_following(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowerListResponse:
    return await follow_service.get_following(
        db, current_user=current_user, skip=skip, limit=limit
    )


@router.get(
    "/followers",
    response_model=FollowerListResponse,
    status_code=status.HTTP_200_OK,
    summary="List accounts following current user",
    description="Fetch paginated list of accounts following the authenticated user.",
)
async def list_followers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowerListResponse:
    return await follow_service.get_followers(
        db, current_user=current_user, skip=skip, limit=limit
    )
