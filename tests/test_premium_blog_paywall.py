"""
Unit tests for Premium Blog Paywall Gating (Task 4.2).
"""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException

from app.models.blog import Blog, BlogStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_get_public_blog_succeeds_without_subscription():
    """Verify non-premium blog reading succeeds for any user."""
    from app.services.blog_service import blog_service

    mock_user = User(id=uuid.uuid4(), username="john", role=UserRole.USER, is_active=True)
    mock_blog = Blog(
        id=uuid.uuid4(),
        title="Public Post",
        content="Free content",
        status=BlogStatus.APPROVED,
        is_premium=False,
        author_id=uuid.uuid4(),
    )
    mock_db = AsyncMock()

    with patch(
        "app.services.blog_service.blog_repository.get_by_id",
        return_value=mock_blog,
    ):
        result = await blog_service.get_blog_by_id(db=mock_db, current_user=mock_user, blog_id=mock_blog.id)
        assert result.id == mock_blog.id


@pytest.mark.asyncio
async def test_get_premium_blog_blocked_for_non_subscriber():
    """Verify premium blog reading raises HTTP 403 for non-subscribers."""
    from app.services.blog_service import blog_service

    mock_user = User(id=uuid.uuid4(), username="john", role=UserRole.USER, is_active=True)
    mock_blog = Blog(
        id=uuid.uuid4(),
        title="VIP Exclusive Post",
        content="Secret premium text",
        status=BlogStatus.APPROVED,
        is_premium=True,
        author_id=uuid.uuid4(),
    )
    mock_db = AsyncMock()

    with patch(
        "app.services.blog_service.blog_repository.get_by_id",
        return_value=mock_blog,
    ), patch(
        "app.services.blog_service.require_active_subscription",
        side_effect=HTTPException(status_code=403, detail="Active VIP Subscription required to access premium content."),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await blog_service.get_blog_by_id(db=mock_db, current_user=mock_user, blog_id=mock_blog.id)
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_premium_blog_allowed_for_admin():
    """Verify premium blog reading succeeds for Admin role."""
    from app.services.blog_service import blog_service

    admin_user = User(id=uuid.uuid4(), username="admin", role=UserRole.ADMIN, is_active=True)
    mock_blog = Blog(
        id=uuid.uuid4(),
        title="VIP Exclusive Post",
        content="Secret premium text",
        status=BlogStatus.APPROVED,
        is_premium=True,
        author_id=uuid.uuid4(),
    )
    mock_db = AsyncMock()

    with patch(
        "app.services.blog_service.blog_repository.get_by_id",
        return_value=mock_blog,
    ), patch(
        "app.services.blog_service.require_active_subscription",
        return_value=admin_user,
    ):
        result = await blog_service.get_blog_by_id(db=mock_db, current_user=admin_user, blog_id=mock_blog.id)
        assert result.id == mock_blog.id
