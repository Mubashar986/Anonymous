"""
Unit tests for Subscription Lifecycle Event Handlers (Task 3.2).
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.user import User, UserRole
from app.models.subscription import Subscription


@pytest.mark.asyncio
async def test_handle_unhandled_event(monkeypatch):
    """Verify unhandled event types are safely ignored without raising error."""
    from app.services.billing_service import billing_service
    mock_db = AsyncMock()

    event = {
        "id": "evt_test_unhandled",
        "type": "payment_intent.succeeded",
        "data": {"object": {}},
    }

    result = await billing_service.handle_webhook_event(db=mock_db, event=event)
    assert result["status"] == "success"
    assert result["event_type"] == "payment_intent.succeeded"


@pytest.mark.asyncio
async def test_handle_subscription_deleted_event(monkeypatch):
    """Verify customer.subscription.deleted marks subscription status as canceled."""
    from app.services.billing_service import billing_service
    mock_db = AsyncMock()

    test_user_id = uuid.uuid4()
    mock_sub = Subscription(
        user_id=test_user_id,
        stripe_customer_id="cus_test_123",
        stripe_subscription_id="sub_test_123",
        stripe_price_id="price_premium_monthly",
        status="active",
        cancel_at_period_end=False,
    )

    with patch(
        "app.services.billing_service.subscription_repository.get_by_stripe_subscription_id",
        return_value=mock_sub,
    ), patch(
        "app.services.billing_service.subscription_repository.upsert_subscription",
        new_callable=AsyncMock,
    ) as mock_upsert:
        event = {
            "id": "evt_test_deleted",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                }
            },
        }

        result = await billing_service.handle_webhook_event(db=mock_db, event=event)
        assert result["status"] == "success"
        mock_upsert.assert_called_once()
        kwargs = mock_upsert.call_args.kwargs
        assert kwargs["status"] == "canceled"
        assert kwargs["cancel_at_period_end"] is True


class MockStripeSubscription:
    """Mock class simulating stripe-python SDK Subscription model which doesn't have .get() but has .to_dict()."""
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data

    def __getattr__(self, name):
        if name == "get":
            raise AttributeError("'MockStripeSubscription' object has no attribute 'get'")
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'MockStripeSubscription' object has no attribute '{name}'")


@pytest.mark.asyncio
async def test_handle_checkout_session_completed_realistic_stripe_object(monkeypatch):
    """Verify handle_checkout_session_completed successfully processes non-dict StripeObject via to_dict()."""
    from app.services.billing_service import billing_service
    mock_db = AsyncMock()

    test_user_id = uuid.uuid4()
    mock_user = User(
        id=test_user_id,
        email="user@example.com",
        username="testuser",
        stripe_customer_id="cus_test_123"
    )

    # Realistic mock subscription data representing Stripe SDK's returned object
    sub_data = {
        "id": "sub_test_123",
        "customer": "cus_test_123",
        "status": "active",
        "cancel_at_period_end": False,
        "current_period_end": 1772457600,  # Some timestamp
        "items": {
            "data": [
                {
                    "price": {
                        "id": "price_premium_monthly"
                    }
                }
            ]
        }
    }
    mock_stripe_sub = MockStripeSubscription(sub_data)

    mock_stripe_client = MagicMock()
    mock_stripe_client.Subscription.retrieve.return_value = mock_stripe_sub

    with patch(
        "app.services.billing_service.get_stripe_client",
        return_value=mock_stripe_client
    ), patch(
        "app.services.billing_service.user_repository.get_by_id",
        new_callable=AsyncMock,
        return_value=mock_user
    ), patch(
        "app.services.billing_service.subscription_repository.upsert_subscription",
        new_callable=AsyncMock
    ) as mock_upsert:
        event = {
            "id": "evt_test_checkout",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "metadata": {
                        "user_id": str(test_user_id)
                    }
                }
            }
        }

        result = await billing_service.handle_webhook_event(db=mock_db, event=event)
        assert result["status"] == "success"
        
        # Verify it retrieved the correct subscription id from Stripe
        mock_stripe_client.Subscription.retrieve.assert_called_once_with("sub_test_123")
        
        # Verify upsert_subscription is called with CORRECT parsed data
        mock_upsert.assert_called_once()
        kwargs = mock_upsert.call_args.kwargs
        assert kwargs["user_id"] == test_user_id
        assert kwargs["stripe_customer_id"] == "cus_test_123"
        assert kwargs["stripe_subscription_id"] == "sub_test_123"
        assert kwargs["status"] == "active"
        assert kwargs["cancel_at_period_end"] is False
        assert kwargs["stripe_price_id"] == "price_premium_monthly"
        assert kwargs["current_period_end"] is not None
        assert kwargs["current_period_end"].timestamp() == 1772457600

