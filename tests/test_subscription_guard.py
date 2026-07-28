"""
Unit tests for Subscription Guard Dependency (Task 4.1).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.subscription import Subscription


@pytest.mark.asyncio
async def test_admin_bypasses_subscription_guard():
    """Verify Admin role bypasses subscription check entirely."""
    from app.dependencies.auth import require_active_subscription

    admin_user = User(id=uuid.uuid4(), username="admin", role=UserRole.ADMIN, is_active=True)
    mock_db = AsyncMock()

    result = await require_active_subscription(current_user=admin_user, db=mock_db)
    assert result.id == admin_user.id


@pytest.mark.asyncio
async def test_active_subscriber_access_granted():
    """Verify user with active unexpired subscription is granted access."""
    from app.dependencies.auth import require_active_subscription

    normal_user = User(id=uuid.uuid4(), username="john", role=UserRole.USER, is_active=True)
    mock_db = AsyncMock()
    mock_sub = Subscription(
        user_id=normal_user.id,
        status="active",
        current_period_end=datetime.now(timezone.utc) + timedelta(days=15),
    )

    with patch(
        "app.dependencies.auth.subscription_repository.get_by_user_id",
        return_value=mock_sub,
    ):
        result = await require_active_subscription(current_user=normal_user, db=mock_db)
        assert result.id == normal_user.id


@pytest.mark.asyncio
async def test_non_subscriber_access_denied():
    """Verify user with no subscription is denied with HTTP 403."""
    from app.dependencies.auth import require_active_subscription

    normal_user = User(id=uuid.uuid4(), username="john", role=UserRole.USER, is_active=True)
    mock_db = AsyncMock()

    with patch(
        "app.dependencies.auth.subscription_repository.get_by_user_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await require_active_subscription(current_user=normal_user, db=mock_db)
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_canceled_subscriber_access_denied():
    """Verify user with canceled subscription is denied with HTTP 403."""
    from app.dependencies.auth import require_active_subscription

    normal_user = User(id=uuid.uuid4(), username="john", role=UserRole.USER, is_active=True)
    mock_db = AsyncMock()
    mock_sub = Subscription(
        user_id=normal_user.id,
        status="canceled",
        current_period_end=datetime.now(timezone.utc) - timedelta(days=1),
    )

    with patch(
        "app.dependencies.auth.subscription_repository.get_by_user_id",
        return_value=mock_sub,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await require_active_subscription(current_user=normal_user, db=mock_db)
        assert exc_info.value.status_code == 403
