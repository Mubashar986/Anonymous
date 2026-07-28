"""
Unit tests for Notification Event Taxonomy, Payloads, and Idempotency Rules.
"""

import uuid
import pytest
from pydantic import ValidationError
from app.schemas.notification import (
    NotificationTypeEnum,
    NavigationTargetEnum,
    NotificationPayloadSchema,
    should_suppress_actor_recipient,
    build_idempotency_key,
)


def test_notification_type_enum_values():
    """Assert all 8 v1 event types are present."""
    expected_types = {
        "new_follower",
        "new_direct_message",
        "blog_approved",
        "blog_rejected",
        "room_request_approved",
        "room_request_rejected",
        "role_changed",
        "permission_override_changed",
    }
    actual_types = {item.value for item in NotificationTypeEnum}
    assert actual_types == expected_types


def test_should_suppress_actor_recipient():
    """Assert self-notifications return True for suppression."""
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    assert should_suppress_actor_recipient(user_id, user_id) is True
    assert should_suppress_actor_recipient(user_id, other_id) is False


def test_build_idempotency_key():
    """Assert key generation format is deterministic."""
    actor_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    recipient_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    target_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    key = build_idempotency_key(
        NotificationTypeEnum.NEW_FOLLOWER,
        actor_id,
        recipient_id,
        target_id,
    )
    assert key == "new_follower:11111111-1111-1111-1111-111111111111:22222222-2222-2222-2222-222222222222:33333333-3333-3333-3333-333333333333"


def test_notification_payload_schema_valid():
    """Assert valid payload passes Pydantic validation."""
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()
    payload = NotificationPayloadSchema(
        actor_id=actor_id,
        actor_username="alice",
        target_type="user",
        target_id=target_id,
        summary_text="@alice started following you.",
        navigation_target=NavigationTargetEnum.PROFILE,
        navigation_params={"user_id": str(target_id)},
    )
    assert payload.actor_username == "alice"
    assert payload.navigation_target == NavigationTargetEnum.PROFILE


def test_notification_payload_schema_extra_fields_forbidden():
    """Assert extra un-sanitized fields trigger ValidationError."""
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        NotificationPayloadSchema(
            actor_id=actor_id,
            actor_username="alice",
            target_type="user",
            target_id=target_id,
            navigation_target=NavigationTargetEnum.PROFILE,
            email="leak@example.com",  # Extra forbidden field
        )
