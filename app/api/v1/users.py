"""
API Router for User Profile Endpoints.

Handles protected user profile viewing and account details updating.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from app.database.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.permission import PermissionAuditLog
from app.repositories import user_repository
from app.schemas.follow import FollowerListResponse
from app.schemas.user import UserResponse, UserRoleUpdate, UserUpdate, UserProfileResponse
from app.schemas.permission import UserCapabilitiesResponse, UserOverrideUpdateRequest, PermissionAuditLogResponse
from app.services.follow_service import follow_service
from app.services.profile_service import profile_service
from app.services.policy_service import policy_evaluator
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/discover",
    response_model=FollowerListResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover accounts eligible to follow",
    description="Fetch list of user and writer accounts eligible to follow, with current follow state.",
)
async def discover_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FollowerListResponse:
    return await follow_service.discover_users(
        db, current_user=current_user, skip=skip, limit=limit
    )


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
    description="Admin-only endpoint to view registered platform users.",
)
async def list_users_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    return await user_repository.get_all(db, skip=skip, limit=limit)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Fetch the authenticated user's profile information.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update username or email address for the authenticated user.",
)
async def update_my_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    updated_user = await user_repository.update(db, current_user, user_in)
    return updated_user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign role to user (Admin only)",
    description="Allows an Admin to promote or modify a user's role (admin, writer, user).",
)
async def update_user_role(
    user_id: uuid.UUID,
    role_in: UserRoleUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    target_user = await user_repository.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )
    updated_user = await user_repository.update_role(db, db_user=target_user, role=role_in.role)

    # Emit ROLE_CHANGED notification
    await notification_service.create_notification_event(
        db=db,
        recipient_id=target_user.id,
        actor_id=current_user.id,
        actor_username=current_user.username,
        event_type=NotificationTypeEnum.ROLE_CHANGED,
        target_type="user",
        target_id=target_user.id,
        title="Role Updated",
        summary_text=f"Your role was updated to '{role_in.role.value}'.",
        navigation_target=NavigationTargetEnum.PROFILE,
        navigation_params={"user_id": str(target_user.id)},
    )

    return updated_user


@router.patch(
    "/{user_id}/verify",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle user verification status (Admin only)",
    description="Allows an Admin to manually verify or unverify a user account.",
)
async def toggle_user_verification(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    target_user = await user_repository.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )
    return await user_repository.toggle_verification(db, db_user=target_user)


@router.get(
    "/{user_id}/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Fetch safe public profile information of another user/writer.",
)
async def get_user_profile(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    return await profile_service.get_user_profile(
        db, target_id=user_id, viewer_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/{user_id}/permissions",
    response_model=UserCapabilitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user capabilities (Admin only)",
    description="Allows an Admin to view a target user's capabilities, defaults, and overrides.",
)
async def get_user_permissions(
    user_id: uuid.UUID,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserCapabilitiesResponse:
    target_user = await user_repository.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    caps = await policy_evaluator.get_user_capabilities(db, target_user)
    return UserCapabilitiesResponse(user_id=user_id, capabilities=caps)


@router.put(
    "/{user_id}/permissions",
    status_code=status.HTTP_200_OK,
    summary="Set capability override for user (Admin only)",
    description="Allows an Admin to set explicit allow/deny/inherit overrides for a user capability.",
)
async def set_user_permission_override(
    user_id: uuid.UUID,
    request_data: UserOverrideUpdateRequest,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    target_user = await user_repository.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    await policy_evaluator.set_user_override(
        db=db,
        actor=admin,
        target_user=target_user,
        capability=request_data.capability,
        effect=request_data.effect,
        reason=request_data.reason,
    )
    return {"message": "Permission override updated successfully."}


@router.get(
    "/{user_id}/permissions/audit",
    response_model=List[PermissionAuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user permission audit logs (Admin only)",
    description="Fetch permission change audit history for a target user.",
)
async def get_user_permission_audit_logs(
    user_id: uuid.UUID,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[PermissionAuditLogResponse]:
    target_user = await user_repository.get_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    stmt = select(PermissionAuditLog).where(
        PermissionAuditLog.target_id == user_id
    ).order_by(PermissionAuditLog.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

