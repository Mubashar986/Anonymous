"""
Tests for Stripe configuration and client initialization (Task 1.2).
"""

import pytest
from app.core.config import settings
from app.core.stripe_client import is_stripe_configured, get_stripe_client


def test_stripe_settings_exist():
    """Verify Stripe setting fields exist on settings object."""
    assert hasattr(settings, "STRIPE_SECRET_KEY")
    assert hasattr(settings, "STRIPE_WEBHOOK_SECRET")
    assert hasattr(settings, "STRIPE_PRICE_PREMIUM_MONTHLY")


def test_stripe_client_import():
    """Verify stripe client module can be obtained."""
    client = get_stripe_client()
    assert client is not None
