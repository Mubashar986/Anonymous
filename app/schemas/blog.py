"""
Pydantic schemas for Blog request validation and response serialization.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.blog import BlogStatus


class BlogBase(BaseModel):
    """
    Base Blog schema containing common fields.
    """
    title: str = Field(..., min_length=3, max_length=255, description="Blog post title")
    content: str = Field(..., min_length=5, description="Full blog content body")
    is_premium: bool = Field(False, description="Flag indicating subscriber-only VIP content")


class BlogCreate(BlogBase):
    """
    Schema for creating a new Blog post.
    """
    pass


class BlogUpdate(BaseModel):
    """
    Schema for updating an existing Blog post.
    """
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Updated title")
    content: Optional[str] = Field(None, min_length=5, description="Updated content")
    is_premium: Optional[bool] = Field(None, description="Updated premium status")


class BlogApprove(BaseModel):
    """
    Schema for admin blog approval/rejection.
    """
    status: BlogStatus = Field(..., description="Approval status: approved or rejected")


class BlogResponse(BlogBase):
    """
    Schema for returning Blog post details in API responses.
    """
    id: uuid.UUID
    status: BlogStatus
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
