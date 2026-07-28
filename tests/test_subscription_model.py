"""
Unit tests for Subscription model and User extension (Task 1.3).
"""

import pytest
from app.models.user import User
from app.models.subscription import Subscription


def test_subscription_model_attributes():
    """Verify Subscription ORM class attributes."""
    assert hasattr(Subscription, "id")
    assert hasattr(Subscription, "user_id")
    assert hasattr(Subscription, "stripe_customer_id")
    assert hasattr(Subscription, "stripe_subscription_id")
    assert hasattr(Subscription, "stripe_price_id")
    assert hasattr(Subscription, "status")
    assert hasattr(Subscription, "current_period_end")
    assert hasattr(Subscription, "cancel_at_period_end")


def test_user_stripe_customer_id_attribute():
    """Verify User model has stripe_customer_id attribute."""
    assert hasattr(User, "stripe_customer_id")
    assert hasattr(User, "subscription")
