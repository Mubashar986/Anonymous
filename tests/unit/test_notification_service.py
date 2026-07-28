"""
Unit tests for NotificationService helper methods and suppression logic.
"""

import uuid
import pytest
from app.schemas.notification import (
    NotificationTypeEnum,
    NavigationTargetEnum,
    should_suppress_actor_recipient,
    build_idempotency_key,
)
from app.services.notification_service import notification_service


def test_actor_suppression_logic():
    """Assert actor == recipient returns True for suppression."""
    same_id = uuid.uuid4()
    diff_id = uuid.uuid4()
    assert should_suppress_actor_recipient(same_id, same_id) is True
    assert should_suppress_actor_recipient(same_id, diff_id) is False


def test_idempotency_key_formatting():
    """Assert key generation produces expected format."""
    actor_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    recipient_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    target_id = uuid.UUID("33333333-3333-3333-3333-333333333333")

    key = build_idempotency_key(
        event_type=NotificationTypeEnum.NEW_FOLLOWER,
        actor_id=actor_id,
        recipient_id=recipient_id,
        target_id=target_id,
    )
    assert key == f"new_follower:{actor_id}:{recipient_id}:{target_id}"
