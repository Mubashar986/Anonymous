"""
Service Layer for Authentication business logic.

Coordinates repositories, security utilities, and email services to perform user registration,
authentication, token rotation, password recovery, and session management.
Includes robust error handling to ensure email failures do not crash API requests.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_password_reset_email, send_verification_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories import token_repository, user_repository
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """
    Business Logic Service for Authentication workflows.
    """

    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        Register a new user account:
        1. Check email uniqueness
        2. Check username uniqueness
        3. Hash password
        4. Persist user record
        5. Dispatch verification email (non-blocking: failure doesn't crash signup)
        """
        existing_email = await user_repository.get_by_email(db, user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        existing_username = await user_repository.get_by_username(db, user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )

        hashed_pwd = get_password_hash(user_in.password)
        user = await user_repository.create(db, user_in, hashed_pwd)

        # Email dispatch is non-critical: dispatch asynchronously in background
        # so SMTP connection delays never block or hang user signup HTTP responses
        try:
            import asyncio
            verification_token = create_access_token(
                subject=user.id,
                expires_delta=None,  # Uses default expiration
            )
            asyncio.create_task(send_verification_email(email_to=user.email, token=verification_token))
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")

        return user   # Do NOT re-raise — user account was created successfully

    async def authenticate_user(self, db: AsyncSession, login_in: LoginRequest) -> Token:
        """
        Authenticate user credentials and issue Access & Refresh tokens.
        """
        user = await user_repository.get_by_email(db, login_in.email)
        if not user or not verify_password(login_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive. Please contact support.",
            )

        access_token = create_access_token(subject=user.id)
        refresh_token_str = create_refresh_token(subject=user.id)

        # Decode refresh token payload to extract expiration date for DB storage
        payload = decode_token(refresh_token_str)
        exp_timestamp = payload["exp"]
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        # Persist refresh token session in database
        await token_repository.create(
            db=db,
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
        )

    async def refresh_tokens(self, db: AsyncSession, refresh_token_str: str) -> Token:
        """
        Rotate Refresh Token and issue a new Access Token pair.
        Implements Refresh Token Rotation to prevent token theft reuse.
        """
        try:
            payload = decode_token(refresh_token_str)
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )

        db_token = await token_repository.get_by_token(db, refresh_token_str)
        if not db_token or db_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked.",
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired.",
            )

        user = await user_repository.get_by_id(db, db_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or deleted.",
            )

        # Revoke current refresh token (Rotation)
        await token_repository.revoke(db, db_token)

        # Issue new pair
        new_access_token = create_access_token(subject=user.id)
        new_refresh_token_str = create_refresh_token(subject=user.id)

        new_payload = decode_token(new_refresh_token_str)
        new_expires_at = datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc)

        await token_repository.create(
            db=db,
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=new_expires_at,
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token_str,
            token_type="bearer",
        )

    async def logout(self, db: AsyncSession, refresh_token_str: str) -> None:
        """
        Revoke an active refresh token session on user logout.
        """
        db_token = await token_repository.get_by_token(db, refresh_token_str)
        if db_token:
            await token_repository.revoke(db, db_token)

    async def verify_email(self, db: AsyncSession, token: str) -> None:
        """
        Confirm user email address using verification token.
        """
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token.",
            )

        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.is_verified:
            return  # Already verified

        user.is_verified = True
        db.add(user)
        await db.commit()

    async def request_password_reset(self, db: AsyncSession, email: str) -> None:
        """
        Initiate password reset flow by emailing a reset token.
        Always returns silently to prevent user enumeration attacks.
        Email failure is caught gracefully — the API still returns 200 OK.
        """
        user = await user_repository.get_by_email(db, email)
        if not user:
            logger.info(f"[FORGOT PASSWORD] Account '{email}' not found in DB — skipping email (Anti-Enumeration 200 OK)")
            return  # Do NOT re-raise — return 200 to prevent user enumeration

        logger.info(f"[FORGOT PASSWORD] Account '{email}' found in DB — dispatching reset email...")
        try:
            reset_token = create_reset_token(subject=user.id)
            await send_password_reset_email(email_to=user.email, token=reset_token)
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")

    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> None:
        """
        Reset user password using token and revoke all active refresh tokens.
        """
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )

        # Ensure only dedicated reset tokens can reset passwords
        # Prevents stolen access tokens from being abused
        if token_type != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. A password reset token is required.",
            )

        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        # Update password hash
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()

        # Revoke all active user sessions for security
        await token_repository.revoke_all_for_user(db, user.id)

    async def resend_verification_email(self, db: AsyncSession, email: str) -> None:
        """
        Resend account verification email link to an unverified user.
        Prevents user enumeration by returning silently if user is not found.
        Raises 400 Bad Request if user is already verified.
        """
        user = await user_repository.get_by_email(db, email)
        if not user:
            logger.info(f"[RESEND VERIFICATION] Account '{email}' not found in DB — skipping email (Anti-Enumeration 200 OK)")
            return  # Return silently to prevent user enumeration

        if user.is_verified:
            logger.info(f"[RESEND VERIFICATION] Account '{email}' is already verified.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already verified.",
            )

        logger.info(f"[RESEND VERIFICATION] Account '{email}' unverified — dispatching verification email...")
        try:
            import asyncio
            verification_token = create_access_token(
                subject=user.id,
                expires_delta=None,
            )
            asyncio.create_task(send_verification_email(email_to=user.email, token=verification_token))
        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {e}")


# Singleton instance
auth_service = AuthService()
