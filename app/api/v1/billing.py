"""
API Router for Billing Endpoints.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.billing import BillingPortalResponse, CheckoutSessionResponse, SubscriptionStatusResponse
from app.services.billing_service import billing_service

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Stripe Checkout Session",
    description="Initiates a hosted Stripe Checkout payment session for subscription upgrade.",
)
async def create_checkout_session(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session for the authenticated user.
    """
    return await billing_service.create_checkout_session(db=db, user=current_user)


@router.post(
    "/create-portal-session",
    response_model=BillingPortalResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Stripe Customer Portal Session",
    description="Initiates a self-serve Stripe Customer Portal session for managing subscriptions and payment methods.",
)
async def create_portal_session(
    current_user: User = Depends(get_current_active_user),
) -> BillingPortalResponse:
    """
    Create a Customer Portal Session for the authenticated user.
    """
    return await billing_service.create_portal_session(user=current_user)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe Webhook Listener",
    description="Public webhook endpoint invoked by Stripe to deliver signed payment events.",
)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive and cryptographically verify Stripe webhook events.
    """
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header."
        )

    payload_bytes = await request.body()
    event = await billing_service.process_webhook(
        payload_bytes=payload_bytes, sig_header=sig_header
    )
    return await billing_service.handle_webhook_event(db=db, event=event)


@router.get(
    "/me",
    response_model=SubscriptionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Subscription Status",
    description="Retrieve subscription plan details and Stripe billing status for the authenticated user.",
)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatusResponse:
    """
    Get current subscription details for the authenticated user.
    """
    return await billing_service.get_subscription_status(db=db, user=current_user)

