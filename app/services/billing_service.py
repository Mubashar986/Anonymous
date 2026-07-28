"""
Billing Service Layer.

Encapsulates Stripe API interactions for Checkout Sessions, Customer provisioning,
and Billing Portal management.
"""

import logging
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import stripe

from app.core.config import settings
from app.core.stripe_client import is_stripe_configured, get_stripe_client
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.repositories.subscription_repository import subscription_repository
from app.schemas.billing import BillingPortalResponse, CheckoutSessionResponse, SubscriptionStatusResponse

logger = logging.getLogger(__name__)


class BillingService:
    """
    Business logic service for Stripe billing integration.
    """

    async def get_or_create_stripe_customer(self, db: AsyncSession, user: User) -> str:
        """
        Retrieve existing stripe_customer_id or create a new Stripe Customer.
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        stripe_sdk = get_stripe_client()
        try:
            customer = stripe_sdk.Customer.create(
                email=user.email,
                name=user.username,
                metadata={"user_id": str(user.id)},
            )
            customer_id = customer["id"]
            await user_repository.update_stripe_customer_id(
                db=db, db_user=user, stripe_customer_id=customer_id
            )
            logger.info(f"Created Stripe Customer {customer_id} for user {user.id}")
            return customer_id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Customer creation error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to provision payment profile: {e.user_message or str(e)}"
            )

    async def create_checkout_session(
        self, db: AsyncSession, user: User
    ) -> CheckoutSessionResponse:
        """
        Create a Stripe Checkout Session for subscription upgrade.
        """
        if not is_stripe_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe billing is not configured in this environment."
            )

        if not settings.STRIPE_PRICE_PREMIUM_MONTHLY or settings.STRIPE_PRICE_PREMIUM_MONTHLY.endswith("placeholder"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe price ID is missing or set to placeholder."
            )

        customer_id = await self.get_or_create_stripe_customer(db=db, user=user)
        stripe_sdk = get_stripe_client()

        try:
            session = stripe_sdk.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": settings.STRIPE_PRICE_PREMIUM_MONTHLY,
                        "quantity": 1,
                    }
                ],
                success_url=f"{settings.FRONTEND_URL}/pricing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/pricing",
                metadata={
                    "user_id": str(user.id),
                },
            )
            logger.info(f"Created Checkout Session {session.id} for user {user.id}")
            return CheckoutSessionResponse(checkout_url=session.url)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Checkout Session error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create checkout session: {e.user_message or str(e)}"
            )

    async def create_portal_session(self, user: User) -> BillingPortalResponse:
        """
        Create a Stripe Customer Portal session for subscription management.
        """
        if not is_stripe_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe billing is not configured in this environment."
            )

        if not user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing profile found for this account. Please subscribe first."
            )

        stripe_sdk = get_stripe_client()

        try:
            session = stripe_sdk.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=f"{settings.FRONTEND_URL}/pricing",
            )
            logger.info(f"Created Customer Portal Session {session.id} for user {user.id}")
            return BillingPortalResponse(portal_url=session.url)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe Customer Portal error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create portal session: {e.user_message or str(e)}"
            )

    async def process_webhook(self, payload_bytes: bytes, sig_header: str) -> dict:
        """
        Verify Stripe webhook signature and return constructed event object.
        """
        if not is_stripe_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe billing is not configured in this environment."
            )

        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret or webhook_secret.endswith("placeholder"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe webhook secret is missing or set to placeholder."
            )

        stripe_sdk = get_stripe_client()

        try:
            event = stripe_sdk.Webhook.construct_event(
                payload=payload_bytes,
                sig_header=sig_header,
                secret=webhook_secret,
            )
            event_dict = event.to_dict() if hasattr(event, "to_dict") else (event if isinstance(event, dict) else dict(event))
            logger.info(f"Verified Stripe Webhook event {event_dict.get('id')} ({event_dict.get('type')})")
            return event_dict
        except ValueError as e:
            logger.warning(f"Invalid webhook payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Invalid webhook signature: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook signature: {str(e)}"
            )

    async def handle_webhook_event(self, db: AsyncSession, event: dict) -> dict:
        """
        Process verified Stripe event and synchronize local DB subscription status with error resilience.
        """
        event_id = getattr(event, "id", None) or (event.get("id") if isinstance(event, dict) else None)
        event_type = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else None)
        if isinstance(event, dict):
            data_object = event.get("data", {}).get("object", {})
        else:
            data_object = getattr(getattr(event, "data", None), "object", {})

        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_session_completed(db, data_object)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(db, data_object)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(db, data_object)
            else:
                logger.info(f"Unhandled Stripe event type ignored: {event_type} (event_id: {event_id})")

            logger.info(f"Successfully processed webhook event {event_id} ({event_type})")
            return {"status": "success", "event_id": event_id, "event_type": event_type}
        except SQLAlchemyError as e:
            logger.error(f"Database error processing webhook event {event_id} ({event_type}): {e}")
            try:
                await db.rollback()
            except Exception as rollback_err:
                logger.error(f"Failed to rollback transaction for event {event_id}: {rollback_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error processing payment notification."
            )
        except Exception as e:
            logger.error(f"Unexpected error processing webhook event {event_id} ({event_type}): {e}", exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook event."
            )

    async def _handle_checkout_session_completed(self, db: AsyncSession, session: dict):
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        metadata = session.get("metadata", {}) or {}
        user_id_str = metadata.get("user_id")

        db_user = None
        if user_id_str:
            try:
                db_user = await user_repository.get_by_id(db, uuid.UUID(user_id_str))
            except Exception as e:
                logger.warning(f"Failed to lookup user by metadata user_id {user_id_str}: {e}")

        if not db_user and customer_id:
            db_user = await user_repository.get_by_stripe_customer_id(db, customer_id)

        if not db_user:
            logger.error(f"Cannot process checkout.session.completed: No user found for customer {customer_id}")
            return

        if customer_id and not db_user.stripe_customer_id:
            await user_repository.update_stripe_customer_id(db, db_user, customer_id)

        stripe_price_id = settings.STRIPE_PRICE_PREMIUM_MONTHLY
        current_period_end = None
        status_str = "active"
        cancel_at_period_end = False

        if subscription_id:
            stripe_sdk = get_stripe_client()
            try:
                stripe_sub = stripe_sdk.Subscription.retrieve(subscription_id)
                stripe_sub_dict = stripe_sub.to_dict() if hasattr(stripe_sub, "to_dict") else (stripe_sub if isinstance(stripe_sub, dict) else dict(stripe_sub))
                status_str = stripe_sub_dict.get("status", "active")
                cancel_at_period_end = stripe_sub_dict.get("cancel_at_period_end", False)
                items = stripe_sub_dict.get("items", {}).get("data", [])
                if items:
                    stripe_price_id = items[0].get("price", {}).get("id", stripe_price_id)
                period_end_ts = stripe_sub_dict.get("current_period_end")
                if period_end_ts:
                    current_period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)
            except Exception as e:
                logger.error(f"Failed to retrieve subscription {subscription_id} from Stripe: {e}")

        await subscription_repository.upsert_subscription(
            db=db,
            user_id=db_user.id,
            stripe_customer_id=customer_id or db_user.stripe_customer_id or "",
            stripe_subscription_id=subscription_id or "",
            stripe_price_id=stripe_price_id,
            status=status_str,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )
        logger.info(f"Successfully activated subscription for user {db_user.id}")

    async def _handle_subscription_updated(self, db: AsyncSession, subscription: dict):
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status_str = subscription.get("status", "active")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        period_end_ts = subscription.get("current_period_end")
        current_period_end = (
            datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if period_end_ts else None
        )

        items = subscription.get("items", {}).get("data", [])
        price_id = items[0].get("price", {}).get("id", "") if items else ""

        db_sub = await subscription_repository.get_by_stripe_subscription_id(db, subscription_id)
        if not db_sub and customer_id:
            db_user = await user_repository.get_by_stripe_customer_id(db, customer_id)
            if db_user:
                db_sub = await subscription_repository.get_by_user_id(db, db_user.id)

        if db_sub:
            await subscription_repository.upsert_subscription(
                db=db,
                user_id=db_sub.user_id,
                stripe_customer_id=customer_id or db_sub.stripe_customer_id,
                stripe_subscription_id=subscription_id,
                stripe_price_id=price_id or db_sub.stripe_price_id,
                status=status_str,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
            )
            logger.info(f"Updated subscription {subscription_id} to status={status_str}")
        else:
            logger.warning(f"Subscription updated event received for unknown subscription {subscription_id}")

    async def _handle_subscription_deleted(self, db: AsyncSession, subscription: dict):
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")

        db_sub = await subscription_repository.get_by_stripe_subscription_id(db, subscription_id)
        if not db_sub and customer_id:
            db_user = await user_repository.get_by_stripe_customer_id(db, customer_id)
            if db_user:
                db_sub = await subscription_repository.get_by_user_id(db, db_user.id)

        if db_sub:
            await subscription_repository.upsert_subscription(
                db=db,
                user_id=db_sub.user_id,
                stripe_customer_id=customer_id or db_sub.stripe_customer_id,
                stripe_subscription_id=subscription_id,
                stripe_price_id=db_sub.stripe_price_id,
                status="canceled",
                current_period_end=db_sub.current_period_end,
                cancel_at_period_end=True,
            )
            logger.info(f"Marked subscription {subscription_id} as canceled for user {db_sub.user_id}")
        else:
            logger.warning(f"Subscription deleted event received for unknown subscription {subscription_id}")

    async def get_subscription_status(
        self, db: AsyncSession, user: User
    ) -> SubscriptionStatusResponse:
        """
        Retrieve subscription status details for a user.
        """
        subscription = await subscription_repository.get_by_user_id(db, user.id)
        if not subscription:
            return SubscriptionStatusResponse(
                plan="free",
                status="inactive",
                stripe_customer_id=user.stripe_customer_id,
                stripe_subscription_id=None,
                current_period_end=None,
                cancel_at_period_end=False,
            )

        is_premium = False
        if subscription.status == "active":
            is_premium = True
            if subscription.current_period_end:
                now = datetime.now(timezone.utc)
                period_end = subscription.current_period_end
                if period_end.tzinfo is None:
                    period_end = period_end.replace(tzinfo=timezone.utc)
                if period_end < now:
                    is_premium = False

        return SubscriptionStatusResponse(
            plan="premium" if is_premium else "free",
            status=subscription.status,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )


# Instantiate singleton service
billing_service = BillingService()

