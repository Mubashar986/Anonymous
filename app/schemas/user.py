"""
Pydantic schemas for User request validation and response formatting.

Uses Pydantic v2 with field validation rules for email, username, and password strength.
"""

import re
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """
    Base user schema containing shared attributes.
    Role is excluded from input schemas to prevent privilege escalation during signup.
    """
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Ensure username contains only alphanumeric characters, underscores, and hyphens.
        """
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain alphanumeric characters, underscores, and hyphens.")
        return v.lower()


class UserCreate(UserBase):
    """
    Schema for User Registration / Signup payload.
    Always creates a standard user role.
    """
    password: str = Field(..., min_length=8, max_length=128, description="User raw password")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password complexity:
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


class UserUpdate(BaseModel):
    """
    Schema for updating User profile attributes.
    Role is intentionally excluded to prevent self-promotion.
    """
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(None, max_length=500, description="Plain text biography description")


class UserRoleUpdate(BaseModel):
    """
    Schema for Admin-only user role modification.
    """
    role: UserRole = Field(..., description="New role to assign to the user (admin, writer, user)")


class UserResponse(UserBase):
    """
    Schema for returning User details in API responses.
    Excludes sensitive fields like hashed_password.
    """
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    # Enables Pydantic to read ORM model instance attributes automatically
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """
    Safe public response schema for social profiles.
    Hides all contact details, verification flags, stripe details, and credentials.
    """
    id: uuid.UUID
    username: str
    role: UserRole
    created_at: datetime
    bio: Optional[str] = None
    followers_count: int
    following_count: int
    is_following: bool
    articles: Optional[List[dict]] = None

    model_config = ConfigDict(from_attributes=True)
