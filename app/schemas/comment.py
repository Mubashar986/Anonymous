"""
Pydantic schemas for Comment request validation and response serialization.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    """
    Base Comment schema containing common fields.
    """
    content: str = Field(..., min_length=1, max_length=2000, description="Comment text body")


class CommentCreate(CommentBase):
    """
    Schema for creating a new Comment on a blog post.
    """
    pass


class CommentUpdate(BaseModel):
    """
    Schema for updating an existing Comment.
    """
    content: str = Field(..., min_length=1, max_length=2000, description="Updated comment text body")


class CommentResponse(CommentBase):
    """
    Schema for returning Comment details in API responses.
    """
    id: uuid.UUID
    blog_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
