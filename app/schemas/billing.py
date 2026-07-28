"""
Pydantic schemas for Billing and Subscription management (Task 2.1).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CheckoutSessionResponse(BaseModel):
    """
    Response schema for POST /api/v1/billing/create-checkout-session.
    """
    checkout_url: str = Field(
        ...,
        description="Hosted Stripe Checkout URL to redirect the user browser to."
    )


class BillingPortalResponse(BaseModel):
    """
    Response schema for POST /api/v1/billing/create-portal-session.
    """
    portal_url: str = Field(
        ...,
        description="Hosted Stripe Customer Billing Portal URL for subscription management."
    )


class SubscriptionStatusResponse(BaseModel):
    """
    Response schema for GET /api/v1/billing/me.
    """
    plan: str = Field(
        default="free",
        description="Subscription plan tier (e.g. 'free' or 'premium')."
    )
    status: str = Field(
        default="inactive",
        description="Stripe subscription status (e.g. 'active', 'inactive', 'canceled', 'past_due')."
    )
    stripe_customer_id: Optional[str] = Field(
        default=None,
        description="Stripe customer ID if available."
    )
    stripe_subscription_id: Optional[str] = Field(
        default=None,
        description="Stripe subscription ID if available."
    )
    current_period_end: Optional[datetime] = Field(
        default=None,
        description="Expiration datetime of current paid billing period."
    )
    cancel_at_period_end: bool = Field(
        default=False,
        description="True if subscription will cancel at current_period_end."
    )

    model_config = ConfigDict(from_attributes=True)
