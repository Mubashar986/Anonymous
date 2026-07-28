"""
Unit tests for Notification SQLAlchemy ORM Model.
"""

import uuid
from app.models.notification import Notification


def test_notification_model_instantiation():
    """Assert Notification model instantiates with defaults."""
    recipient_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    notif = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        event_type="new_follower",
        payload={"actor_username": "alice", "navigation_target": "profile"},
        idempotency_key=f"new_follower:{actor_id}:{recipient_id}:{actor_id}",
        is_read=False,
    )
    assert notif.recipient_id == recipient_id
    assert notif.actor_id == actor_id
    assert notif.event_type == "new_follower"
    assert notif.is_read is False
    assert notif.payload["actor_username"] == "alice"
    assert "new_follower" in notif.idempotency_key
