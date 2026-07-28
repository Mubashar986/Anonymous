"""
Unit tests for Billing Pydantic schemas (Task 2.1).
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.billing import (
    CheckoutSessionResponse,
    BillingPortalResponse,
    SubscriptionStatusResponse,
)


def test_checkout_session_response_valid():
    """Verify CheckoutSessionResponse schema validation happy path."""
    response = CheckoutSessionResponse(checkout_url="https://checkout.stripe.com/pay/cs_test_123")
    assert response.checkout_url == "https://checkout.stripe.com/pay/cs_test_123"
    assert response.model_dump() == {"checkout_url": "https://checkout.stripe.com/pay/cs_test_123"}


def test_checkout_session_response_missing_required():
    """Verify CheckoutSessionResponse fails if checkout_url is omitted."""
    with pytest.raises(ValidationError) as exc_info:
        CheckoutSessionResponse()  # type: ignore
    assert "checkout_url" in str(exc_info.value)


def test_billing_portal_response_valid():
    """Verify BillingPortalResponse schema validation happy path."""
    response = BillingPortalResponse(portal_url="https://billing.stripe.com/p/session/test")
    assert response.portal_url == "https://billing.stripe.com/p/session/test"
    assert response.model_dump() == {"portal_url": "https://billing.stripe.com/p/session/test"}


def test_billing_portal_response_missing_required():
    """Verify BillingPortalResponse fails if portal_url is omitted."""
    with pytest.raises(ValidationError) as exc_info:
        BillingPortalResponse()  # type: ignore
    assert "portal_url" in str(exc_info.value)


def test_subscription_status_response_defaults():
    """Verify SubscriptionStatusResponse default values for free/unsubscribed user."""
    response = SubscriptionStatusResponse()
    assert response.plan == "free"
    assert response.status == "inactive"
    assert response.stripe_customer_id is None
    assert response.stripe_subscription_id is None
    assert response.current_period_end is None
    assert response.cancel_at_period_end is False


def test_subscription_status_response_populated():
    """Verify SubscriptionStatusResponse populated values for active subscriber."""
    now = datetime.now(timezone.utc)
    response = SubscriptionStatusResponse(
        plan="premium",
        status="active",
        stripe_customer_id="cus_test_123",
        stripe_subscription_id="sub_test_456",
        current_period_end=now,
        cancel_at_period_end=True,
    )
    assert response.plan == "premium"
    assert response.status == "active"
    assert response.stripe_customer_id == "cus_test_123"
    assert response.stripe_subscription_id == "sub_test_456"
    assert response.current_period_end == now
    assert response.cancel_at_period_end is True
