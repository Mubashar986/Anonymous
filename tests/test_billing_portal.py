"""
Unit tests for Stripe Customer Portal Endpoint (Task 5.1).
"""

import uuid
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_portal_session_missing_customer_id(monkeypatch):
    """Verify HTTP 400 raised when user has no stripe_customer_id."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: True)
    from app.services.billing_service import billing_service

    mock_user = User(id=uuid.uuid4(), username="john", stripe_customer_id=None)

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.create_portal_session(user=mock_user)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_create_portal_session_unconfigured(monkeypatch):
    """Verify HTTP 503 raised when Stripe is unconfigured."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: False)
    from app.services.billing_service import billing_service

    mock_user = User(id=uuid.uuid4(), username="john", stripe_customer_id="cus_test123")

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.create_portal_session(user=mock_user)
    assert exc_info.value.status_code == 503
