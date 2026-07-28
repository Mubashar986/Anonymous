"""
API Router for Blog Management Endpoints.

Enforces role-based permissions and ownership rules for Admin, Writer, and User roles.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies import get_current_active_user, require_roles, require_capability
from app.models.permission import CapabilityEnum
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.blog import BlogApprove, BlogCreate, BlogResponse, BlogUpdate
from app.services.blog_service import blog_service

router = APIRouter(prefix="/blogs", tags=["Blogs"])


@router.post(
    "",
    response_model=BlogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post",
    description="Writers and Admins can create blog posts. Writer posts default to PENDING approval; Admin posts default to APPROVED.",
)
async def create_blog(
    blog_in: BlogCreate,
    current_user: User = Depends(require_capability(CapabilityEnum.CAN_SUBMIT_BLOG)),
    db: AsyncSession = Depends(get_db),
) -> BlogResponse:

    return await blog_service.create_blog(db=db, current_user=current_user, blog_in=blog_in)


@router.get(
    "",
    response_model=List[BlogResponse],
    status_code=status.HTTP_200_OK,
    summary="List visible blog posts",
    description="Returns blogs based on role visibility rules: Users see APPROVED only; Writers see APPROVED + own posts; Admins see ALL.",
)
async def list_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[BlogResponse]:
    return await blog_service.list_blogs(
        db=db, current_user=current_user, skip=skip, limit=limit
    )


@router.get(
    "/admin/all",
    response_model=List[BlogResponse],
    status_code=status.HTTP_200_OK,
    summary="View all blogs (Admin only)",
    description="Admin-only endpoint to view all blogs regardless of status (pending, approved, rejected).",
)
async def list_all_blogs_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[BlogResponse]:
    return await blog_service.list_all_blogs_admin(
        db=db, current_user=current_user, skip=skip, limit=limit
    )


@router.get(
    "/{blog_id}",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Get blog post details",
    description="Fetch a blog post by ID if visible to the user's role.",
)
async def get_blog_by_id(
    blog_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BlogResponse:
    return await blog_service.get_blog_by_id(
        db=db, current_user=current_user, blog_id=blog_id
    )


@router.patch(
    "/{blog_id}",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a blog post",
    description="Writers can update their own blogs. Admins can update any blog.",
)
async def update_blog(
    blog_id: uuid.UUID,
    blog_in: BlogUpdate,
    current_user: User = Depends(require_roles(UserRole.WRITER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BlogResponse:
    return await blog_service.update_blog(
        db=db, current_user=current_user, blog_id=blog_id, blog_in=blog_in
    )


@router.delete(
    "/{blog_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a blog post",
    description="Writers can delete their own blogs. Admins can delete any blog.",
)
async def delete_blog(
    blog_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.WRITER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await blog_service.delete_blog(db=db, current_user=current_user, blog_id=blog_id)
    return MessageResponse(message="Blog post deleted successfully.")


@router.patch(
    "/{blog_id}/approve",
    response_model=BlogResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve or reject a blog post (Admin only)",
    description="Admins can approve or reject writer blogs.",
)
async def approve_blog(
    blog_id: uuid.UUID,
    approve_in: BlogApprove,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BlogResponse:
    return await blog_service.approve_blog(
        db=db, current_user=current_user, blog_id=blog_id, approve_in=approve_in
    )
