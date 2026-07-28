"""
Repository layer for Subscription entity.
"""

import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.subscription import Subscription


class SubscriptionRepository:
    """
    CRUD operations for Subscription entity.
    """

    async def get_by_user_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalars().first()

    async def get_by_stripe_subscription_id(
        self, db: AsyncSession, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalars().first()

    async def upsert_subscription(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        stripe_price_id: str,
        status: str,
        current_period_end: Optional[datetime] = None,
        cancel_at_period_end: bool = False,
    ) -> Subscription:
        sub = await self.get_by_user_id(db, user_id)
        if not sub:
            sub = await self.get_by_stripe_subscription_id(db, stripe_subscription_id)

        if sub:
            sub.stripe_customer_id = stripe_customer_id
            sub.stripe_subscription_id = stripe_subscription_id
            sub.stripe_price_id = stripe_price_id
            sub.status = status
            sub.current_period_end = current_period_end
            sub.cancel_at_period_end = cancel_at_period_end
        else:
            sub = Subscription(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                stripe_price_id=stripe_price_id,
                status=status,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
            )
            db.add(sub)

        await db.commit()
        await db.refresh(sub)
        return sub


subscription_repository = SubscriptionRepository()
