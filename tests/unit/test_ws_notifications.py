"""
Unit tests asserting WebSocket notification event schemas and payload creation.
"""

import uuid
from app.schemas.ws import (
    WSEventName,
    WSEvent,
    NotificationCreatedPayload,
)


def test_ws_event_name_notification_created():
    """Assert NOTIFICATION_CREATED enum value."""
    assert WSEventName.NOTIFICATION_CREATED == "notification.created"


def test_notification_created_payload_validation():
    """Assert NotificationCreatedPayload schema serialization."""
    notif_id = uuid.uuid4()
    recip_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    payload = NotificationCreatedPayload(
        id=notif_id,
        recipient_id=recip_id,
        actor_id=actor_id,
        event_type="new_follower",
        payload={
            "actor_id": str(actor_id),
            "actor_username": "alice",
            "target_type": "user",
            "target_id": str(actor_id),
            "title": "New Follower",
            "summary_text": "@alice started following you.",
            "navigation_target": "profile",
            "navigation_params": {"user_id": str(actor_id)},
        },
        is_read=False,
        created_at="2026-07-27T12:00:00Z",
    )

    event = WSEvent(
        v=1,
        event=WSEventName.NOTIFICATION_CREATED,
        payload=payload.model_dump(mode="json"),
    )

    data = event.model_dump(mode="json")
    assert data["v"] == 1
    assert data["event"] == "notification.created"
    assert data["payload"]["id"] == str(notif_id)
    assert data["payload"]["event_type"] == "new_follower"
    assert data["payload"]["payload"]["title"] == "New Follower"
