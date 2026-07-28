"""
Service Layer for Emitting & Persisting In-App Notifications.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationTypeEnum,
    NavigationTargetEnum,
    NotificationPayloadSchema,
    should_suppress_actor_recipient,
    build_idempotency_key,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized service for constructing, validating, and persisting notification events.
    """

    async def create_notification_event(
        self,
        db: AsyncSession,
        recipient_id: uuid.UUID,
        actor_id: Optional[uuid.UUID],
        actor_username: str,
        event_type: NotificationTypeEnum,
        target_type: str,
        target_id: uuid.UUID,
        title: Optional[str],
        summary_text: str,
        navigation_target: NavigationTargetEnum,
        navigation_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        """
        Validates payload, suppresses self-notifications, generates idempotency key,
        and persists notification within a nested savepoint transaction.
        """
        # 1. Actor suppression check
        if actor_id and should_suppress_actor_recipient(actor_id, recipient_id):
            logger.info(f"Suppressed self-notification for actor {actor_id}")
            return None

        # 2. Build idempotency key
        idempotency_key = build_idempotency_key(
            event_type=event_type,
            actor_id=actor_id or recipient_id,
            recipient_id=recipient_id,
            target_id=target_id,
        )

        # 3. Build & validate payload schema
        payload_schema = NotificationPayloadSchema(
            actor_id=actor_id or recipient_id,
            actor_username=actor_username,
            target_type=target_type,
            target_id=target_id,
            title=title,
            summary_text=summary_text,
            navigation_target=navigation_target,
            navigation_params=navigation_params or {},
        )

        # 4. Insert notification inside savepoint to isolate DB errors
        created_at_now = datetime.now(timezone.utc)
        try:
            async with db.begin_nested():
                notification = Notification(
                    recipient_id=recipient_id,
                    actor_id=actor_id,
                    event_type=event_type.value,
                    payload=payload_schema.model_dump(mode="json"),
                    is_read=False,
                    idempotency_key=idempotency_key,
                    created_at=created_at_now,
                )
                db.add(notification)
                await db.flush()

            await db.commit()
            await db.refresh(notification)
            logger.info(f"Emitted & committed notification '{event_type.value}' to recipient {recipient_id}")

            # 5. Dispatch realtime WebSocket event to online recipient
            try:
                from app.core.connection_manager import connection_manager
                from app.schemas.ws import WSEvent, WSEventName, NotificationCreatedPayload

                if connection_manager.is_user_online(recipient_id):
                    created_time = (
                        notification.created_at.isoformat()
                        if notification.created_at
                        else created_at_now.isoformat()
                    )
                    ws_payload = NotificationCreatedPayload(
                        id=notification.id,
                        recipient_id=notification.recipient_id,
                        actor_id=notification.actor_id,
                        event_type=notification.event_type,
                        payload=payload_schema.model_dump(mode="json"),
                        is_read=False,
                        created_at=created_time,
                    )
                    ws_event = WSEvent(
                        v=1,
                        event=WSEventName.NOTIFICATION_CREATED,
                        payload=ws_payload.model_dump(mode="json"),
                    )
                    await connection_manager.send_personal_message(
                        ws_event.model_dump(mode="json"), recipient_id
                    )
            except Exception as ws_err:
                logger.warning(f"Failed to dispatch realtime notification WS frame: {ws_err}")

            return notification
        except IntegrityError:
            logger.warning(f"Duplicate notification key '{idempotency_key}' suppressed.")
            return None
        except Exception as e:
            logger.error(f"Error creating notification event: {e}", exc_info=True)
            return None


notification_service = NotificationService()
