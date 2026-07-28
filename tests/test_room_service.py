"""
Unit and Workflow Integration tests for Room Repositories and RoomService.
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import RoomRequestStatus, RoomRequest, Room, RoomMember, RoomMessage
from app.models.user import User, UserRole
from app.models.subscription import Subscription
from app.services.room_service import room_service
from app.repositories.room_repository import (
    room_request_repository,
    room_repository,
    room_member_repository,
    room_message_repository,
)


@pytest.mark.asyncio
async def test_submit_and_approve_room_request_atomic_flow(db_session: AsyncSession):
    """
    Test room request submission by non-admin and atomic approval by admin creating room and adding requester.
    """
    user = User(
        email=f"req_{uuid.uuid4().hex[:6]}@example.com",
        username=f"user_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
        username=f"admin_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user, admin])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(admin)

    req = await room_service.submit_room_request(
        db_session, user, name="Python Engineers", is_private=False
    )
    assert req.id is not None
    assert req.name == "Python Engineers"
    assert req.status == RoomRequestStatus.PENDING
    assert req.requester_id == user.id

    updated_req, room, member = await room_service.approve_room_request(
        db_session, admin, req.id, final_name="Python Engineers Hub"
    )

    assert updated_req.status == RoomRequestStatus.APPROVED
    assert updated_req.decision_by_id == admin.id
    assert room.name == "Python Engineers Hub"
    assert room.is_private is False
    assert member.room_id == room.id
    assert member.user_id == user.id
    assert member.removed_at is None

    with pytest.raises(HTTPException) as exc_info:
        await room_service.approve_room_request(db_session, admin, req.id)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already approved" in exc_info.value.detail


@pytest.mark.asyncio
async def test_reject_room_request_flow(db_session: AsyncSession):
    """
    Test rejecting a room request.
    """
    user = User(
        email=f"req2_{uuid.uuid4().hex[:6]}@example.com",
        username=f"user2_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"admin2_{uuid.uuid4().hex[:6]}@example.com",
        username=f"admin2_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user, admin])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(admin)

    req = await room_service.submit_room_request(
        db_session, user, name="Spam Room", is_private=False
    )
    rejected_req = await room_service.reject_room_request(db_session, admin, req.id)

    assert rejected_req.status == RoomRequestStatus.REJECTED
    assert rejected_req.decision_by_id == admin.id

    req2 = await room_service.submit_room_request(
        db_session, user, name="Another Room", is_private=False
    )
    with pytest.raises(HTTPException) as exc_info:
        await room_service.reject_room_request(db_session, user, req2.id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_public_and_private_room_join_and_subscription_guard(db_session: AsyncSession):
    """
    Test public joins, private paywall subscription requirement, and admin bypass.
    """
    user_free = User(
        email=f"free_{uuid.uuid4().hex[:6]}@example.com",
        username=f"userfree_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    user_paid = User(
        email=f"paid_{uuid.uuid4().hex[:6]}@example.com",
        username=f"userpaid_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"adminvip_{uuid.uuid4().hex[:6]}@example.com",
        username=f"adminvip_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user_free, user_paid, admin])
    await db_session.commit()
    await db_session.refresh(user_free)
    await db_session.refresh(user_paid)
    await db_session.refresh(admin)

    sub = Subscription(
        user_id=user_paid.id,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
        stripe_price_id="price_123",
        status="active",
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    await db_session.commit()

    pub_room = await room_repository.create_room(db_session, name="Public Lounge", is_private=False)
    priv_room = await room_repository.create_room(db_session, name="VIP Platinum Lounge", is_private=True)
    await db_session.commit()

    pub_member = await room_service.join_room(db_session, user_free, pub_room.id)
    assert pub_member.user_id == user_free.id

    with pytest.raises(HTTPException) as exc_info:
        await room_service.join_room(db_session, user_free, priv_room.id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "subscription is required" in exc_info.value.detail

    priv_member = await room_service.join_room(db_session, user_paid, priv_room.id)
    assert priv_member.user_id == user_paid.id

    admin_member = await room_service.join_room(db_session, admin, priv_room.id)
    assert admin_member.user_id == admin.id


@pytest.mark.asyncio
async def test_admin_member_removal_flow(db_session: AsyncSession):
    """
    Test admin member removal and subsequent post/history denial for removed members.
    """
    user = User(
        email=f"rem_{uuid.uuid4().hex[:6]}@example.com",
        username=f"userrem_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"adminrem_{uuid.uuid4().hex[:6]}@example.com",
        username=f"adminrem_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user, admin])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(admin)

    room = await room_repository.create_room(db_session, name="Moderated Room", is_private=False)
    await room_service.join_room(db_session, user, room.id)

    client_msg_id_1 = uuid.uuid4()
    msg1 = await room_service.post_room_message(
        db_session, user, room.id, client_msg_id_1, "Hello room!"
    )
    assert msg1.text == "Hello room!"

    removed_member = await room_service.remove_room_member(db_session, admin, room.id, user.id)
    assert removed_member.removed_at is not None
    assert removed_member.removed_by_id == admin.id

    client_msg_id_2 = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await room_service.post_room_message(
            db_session, user, room.id, client_msg_id_2, "Should fail"
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    with pytest.raises(HTTPException) as exc_info:
        await room_service.get_room_history(db_session, user, room.id)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_room_archival_and_idempotent_messages(db_session: AsyncSession):
    """
    Test archiving room blocks new messages and client_msg_id duplicate idempotency works.
    """
    user = User(
        email=f"arc_{uuid.uuid4().hex[:6]}@example.com",
        username=f"userarc_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"adminarc_{uuid.uuid4().hex[:6]}@example.com",
        username=f"adminarc_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user, admin])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(admin)

    room = await room_repository.create_room(db_session, name="Temp Room", is_private=False)
    await room_service.join_room(db_session, user, room.id)

    client_id = uuid.uuid4()
    msg_a = await room_service.post_room_message(
        db_session, user, room.id, client_id, "First post"
    )

    msg_b = await room_service.post_room_message(
        db_session, user, room.id, client_id, "First post duplicate"
    )
    assert msg_a.id == msg_b.id

    archived_room = await room_service.archive_room(db_session, admin, room.id)
    assert archived_room.is_archived is True

    with pytest.raises(HTTPException) as exc_info:
        await room_service.post_room_message(
            db_session, user, room.id, uuid.uuid4(), "Post after archive"
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "archived room" in exc_info.value.detail
