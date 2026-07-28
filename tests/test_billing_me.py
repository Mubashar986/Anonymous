"""
Unit/integration tests for GET /api/v1/billing/me endpoint (Task 6.3).
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.models.subscription import Subscription


@pytest.mark.asyncio
async def test_get_subscription_status_unauthenticated(client: AsyncClient):
    """Verify endpoint rejects unauthenticated requests with HTTP 401."""
    response = await client.get("/api/v1/billing/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_subscription_status_free_user(client: AsyncClient, db_session: AsyncSession):
    """Verify status response for user without subscription is free/inactive."""
    test_user = User(
        email="free@example.com",
        username="freeuser",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True,
        stripe_customer_id=None
    )
    db_session.add(test_user)
    await db_session.commit()

    token = create_access_token(subject=test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/billing/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert data["stripe_customer_id"] is None
    assert data["stripe_subscription_id"] is None
    assert data["current_period_end"] is None
    assert data["cancel_at_period_end"] is False


@pytest.mark.asyncio
async def test_get_subscription_status_active_premium(client: AsyncClient, db_session: AsyncSession):
    """Verify status response for user with active subscription is premium."""
    test_user = User(
        email="premium@example.com",
        username="premiumuser",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True,
        stripe_customer_id="cus_premium_123"
    )
    db_session.add(test_user)
    await db_session.commit()

    future_date = datetime.now(timezone.utc) + timedelta(days=15)
    
    # We must strip timezone info when saving to db if the model/database uses timezone-naive datetime (SQLAlchemy default timestamp)
    # Let's see: require_active_subscription handles both naive and aware datetimes, but PostgreSQL TIMESTAMP without timezone is standard in SQLAlchemy.
    # Let's save a naive datetime to database to prevent any timezone parsing errors.
    future_date_naive = future_date.replace(tzinfo=None)

    mock_sub = Subscription(
        user_id=test_user.id,
        stripe_customer_id="cus_premium_123",
        stripe_subscription_id="sub_premium_123",
        stripe_price_id="price_premium_monthly",
        status="active",
        current_period_end=future_date_naive,
        cancel_at_period_end=False
    )
    db_session.add(mock_sub)
    await db_session.commit()

    token = create_access_token(subject=test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/billing/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["plan"] == "premium"
    assert data["status"] == "active"
    assert data["stripe_customer_id"] == "cus_premium_123"
    assert data["stripe_subscription_id"] == "sub_premium_123"
    assert data["cancel_at_period_end"] is False
    assert data["current_period_end"] is not None
