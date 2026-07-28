"""
Unit tests for Checkout Session endpoint and Billing Service (Task 2.2).
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_checkout_session_unconfigured(monkeypatch):
    """Verify HTTP 503 raised when Stripe is unconfigured."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: False)
    from app.services.billing_service import billing_service
    mock_db = AsyncMock()
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.create_checkout_session(db=mock_db, user=mock_user)
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_create_checkout_session_missing_price_id(monkeypatch):
    """Verify HTTP 503 raised when Price ID is set to placeholder."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: True)
    monkeypatch.setattr("app.services.billing_service.settings.STRIPE_PRICE_PREMIUM_MONTHLY", "price_placeholder")
    from app.services.billing_service import billing_service
    mock_db = AsyncMock()
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.create_checkout_session(db=mock_db, user=mock_user)
    assert exc_info.value.status_code == 503
