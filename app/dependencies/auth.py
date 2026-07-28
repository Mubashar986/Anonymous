"""
FastAPI Dependency Injection functions for Authentication & Authorization.

Extracts JWT Bearer tokens from incoming requests, verifies signatures, and fetches
the current authenticated user from the database.
"""

import uuid
import jwt
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Callable
from app.core.config import settings
from app.core.security import decode_token
from app.database.database import get_db
from app.models.user import User, UserRole
from app.models.permission import CapabilityEnum
from app.repositories import user_repository
from app.repositories.subscription_repository import subscription_repository
from app.services.policy_service import policy_evaluator

# OAuth2 scheme for extracting Bearer tokens from HTTP Authorization header
# tokenUrl tells Swagger UI where to send login credentials
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)



async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    """
    Dependency to extract Bearer JWT, decode claims, and fetch User entity.
    Raises 401 Unauthorized if token is missing, expired, invalid, or wrong type.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id_str is None or token_type != "access":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = await user_repository.get_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this token no longer exists.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to verify that the authenticated user account is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account.",
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to verify that the authenticated user's email is confirmed.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address not verified. Please check your inbox.",
        )
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory to check if the authenticated user has one of the allowed roles.
    Raises HTTP 403 Forbidden if user role is not permitted.
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized to perform this action.",
            )
        return current_user

    return role_checker


async def require_active_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to verify that the user has an active, unexpired VIP subscription.
    Admins automatically bypass this check.
    Raises HTTP 403 Forbidden if user does not have an active subscription.
    """
    if current_user.role == UserRole.ADMIN:
        return current_user

    subscription = await subscription_repository.get_by_user_id(db, current_user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active VIP Subscription required to access premium content.",
        )

    if subscription.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subscription status is '{subscription.status}'. Active VIP Subscription required.",
        )

    if subscription.current_period_end:
        now = datetime.now(timezone.utc)
        period_end = subscription.current_period_end
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)

        if period_end < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription period has expired. Please renew your VIP subscription.",
            )

    return current_user


def require_capability(capability: CapabilityEnum) -> Callable:
    """
    Dependency factory to check if the current user possesses a specific capability.
    Evaluates active status, admin boundary, per-user overrides, and role defaults.
    """
    async def capability_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        allowed = await policy_evaluator.evaluate_capability(db, current_user, capability)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action denied: user lacks required capability '{capability.value}'.",
            )
        return current_user

    return capability_checker


