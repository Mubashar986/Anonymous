"""
API Router for Comment Management Endpoints.

Handles comment creation, retrieval on blogs, individual comment updating, and deletion.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.comment_service import comment_service

router = APIRouter(tags=["Comments"])


@router.post(
    "/blogs/{blog_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment on a blog post",
    description="Users, Writers, and Admins can comment on approved blog posts.",
)
async def create_comment(
    blog_id: uuid.UUID,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    return await comment_service.create_comment(
        db=db, current_user=current_user, blog_id=blog_id, comment_in=comment_in
    )


@router.get(
    "/blogs/{blog_id}/comments",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="List comments on a blog post",
    description="Fetch comments for a visible blog post.",
)
async def list_comments_for_blog(
    blog_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[CommentResponse]:
    return await comment_service.get_comments_for_blog(
        db=db, current_user=current_user, blog_id=blog_id, skip=skip, limit=limit
    )


@router.get(
    "/comments/admin/all",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="View all comments (Admin only)",
    description="Admin-only endpoint to view all comments across all writer blogs.",
)
async def list_all_comments_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[CommentResponse]:
    return await comment_service.get_all_comments_admin(
        db=db, current_user=current_user, skip=skip, limit=limit
    )


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a comment",
    description="Users and Writers can update their own comments. Admins can update any comment.",
)
async def update_comment(
    comment_id: uuid.UUID,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    return await comment_service.update_comment(
        db=db, current_user=current_user, comment_id=comment_id, comment_in=comment_in
    )


@router.delete(
    "/comments/{comment_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a comment",
    description="Users and Writers can delete their own comments. Admins can delete any comment.",
)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await comment_service.delete_comment(db=db, current_user=current_user, comment_id=comment_id)
    return MessageResponse(message="Comment deleted successfully.")
