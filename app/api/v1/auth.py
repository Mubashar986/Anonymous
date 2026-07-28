"""
API Router for Authentication Endpoints.

Handles user registration, login, token refresh, logout, email verification, and password resets.
"""

from fastapi import APIRouter, Depends, Query, status
from pydantic import EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
)
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Create a new user account with validated credentials and dispatch an account verification email.",
)
async def signup(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await auth_service.register_user(db, user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue tokens",
    description="Authenticates email and password credentials and returns a short-lived Access Token and long-lived Refresh Token.",
)
async def login(
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    tokens = await auth_service.authenticate_user(db, login_in)
    return tokens


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchanges an active Refresh Token for a new Access Token and new Refresh Token (Refresh Token Rotation).",
)
async def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    tokens = await auth_service.refresh_tokens(db, refresh_in.refresh_token)
    return tokens


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user session",
    description="Revokes the provided Refresh Token in the database to terminate the session.",
)
async def logout(
    refresh_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.logout(db, refresh_in.refresh_token)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Validates email verification token and marks user account as verified.",
)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.verify_email(db, token)
    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Sends a password reset token link to the user email. Always returns 200 OK to prevent user enumeration.",
)
async def forgot_password(
    email: str = Query(..., description="Registered email address"),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.request_password_reset(db, email)
    return MessageResponse(message="If the email exists, a password reset link has been sent.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="Resets user password using reset token (sent as JSON body for security) and revokes all existing sessions.",
)
async def reset_password(
    reset_in: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.reset_password(db, reset_in.token, reset_in.new_password)
    return MessageResponse(message="Password reset successfully. Please log in with your new password.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend email verification link",
    description="Resends an account verification link to the specified email address if unverified. Returns 200 OK to prevent user enumeration.",
)
async def resend_verification(
    email: str = Query(..., description="Registered email address"),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.resend_verification_email(db, email)
    return MessageResponse(message="If an unverified account exists for this email, a verification link has been sent.")
