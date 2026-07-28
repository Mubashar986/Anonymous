"""
FastAPI API Routes for Persisted Notifications.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the scalar unread notification count for the authenticated user.
    """
    query = select(func.count(Notification.id)).where(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False,
    )
    result = await db.execute(query)
    unread_count = result.scalar() or 0
    return UnreadCountResponse(unread_count=unread_count)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a paginated list of notifications for the authenticated user.
    """
    base_conditions = [Notification.recipient_id == current_user.id]
    if unread_only:
        base_conditions.append(Notification.is_read == False)

    # Count total matching
    total_stmt = select(func.count(Notification.id)).where(*base_conditions)
    total_res = await db.execute(total_stmt)
    total = total_res.scalar() or 0

    # Count unread overall
    unread_stmt = select(func.count(Notification.id)).where(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False,
    )
    unread_res = await db.execute(unread_stmt)
    unread_count = unread_res.scalar() or 0

    # Fetch items
    offset = (page - 1) * size
    items_stmt = (
        select(Notification)
        .where(*base_conditions)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    items_res = await db.execute(items_stmt)
    notifications = items_res.scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        size=size,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a single notification as read.
    Enforces recipient ownership; returns 404 if not found or not owned.
    """
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()

    if not notification or notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk marks all unread notifications for the authenticated user as read.
    """
    stmt = (
        update(Notification)
        .where(
            Notification.recipient_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return {
        "message": "All notifications marked as read",
        "updated_count": result.rowcount,
    }
