"""
Pydantic schemas for Authentication payloads and token responses.
"""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """
    Schema for User Login request payload.
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """
    Schema for JWT Token pair response returned on successful login or refresh.
    """
    access_token: str = Field(..., description="Short-lived JWT Access Token")
    refresh_token: str = Field(..., description="Long-lived Refresh Token")
    token_type: str = Field("bearer", description="Token authentication type")


class TokenPayload(BaseModel):
    """
    Schema representing decoded JWT payload claims.
    """
    sub: Optional[str] = None  # Subject (User UUID)
    exp: Optional[int] = None  # Expiration timestamp (epoch)
    type: Optional[str] = None  # Token type ('access', 'refresh', or 'reset')


class RefreshTokenRequest(BaseModel):
    """
    Schema for requesting a new Access Token using a Refresh Token.
    """
    refresh_token: str = Field(..., description="Active Refresh Token")


class PasswordResetRequest(BaseModel):
    """
    Schema for resetting a user's password.
    Token and new_password are sent as a JSON body (not URL query params)
    to prevent password leakage in server logs, browser history, and proxies.
    """
    token: str = Field(..., description="Password reset token from email link")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce the same password complexity rules as UserCreate:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class MessageResponse(BaseModel):
    """
    Generic API message response schema.
    """
    message: str = Field(..., description="Status message")
