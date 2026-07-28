"""
Integration tests for Public/Private Room Join Endpoints & Subscription Entitlement Policy.
"""

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.repositories.room_repository import room_repository


@pytest_asyncio.fixture
async def join_policy_users(db_session: AsyncSession):
    """
    Fixture providing free user, paid subscriber user, and admin user with JWT tokens.
    """
    free_user = User(
        email=f"free_{uuid.uuid4().hex[:6]}@example.com",
        username=f"free_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    paid_user = User(
        email=f"paid_{uuid.uuid4().hex[:6]}@example.com",
        username=f"paid_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin_user = User(
        email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
        username=f"admin_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([free_user, paid_user, admin_user])
    await db_session.commit()
    await db_session.refresh(free_user)
    await db_session.refresh(paid_user)
    await db_session.refresh(admin_user)

    # Add active subscription for paid_user
    sub = Subscription(
        user_id=paid_user.id,
        stripe_customer_id="cus_paid_123",
        stripe_subscription_id="sub_paid_123",
        stripe_price_id="price_vip",
        status="active",
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    await db_session.commit()

    # Create public, private, and archived rooms
    pub_room = await room_repository.create_room(db_session, name=f"Public Park {uuid.uuid4().hex[:4]}", is_private=False)
    priv_room = await room_repository.create_room(db_session, name=f"VIP Lounge {uuid.uuid4().hex[:4]}", is_private=True)
    arch_room = await room_repository.create_room(db_session, name=f"Closed Room {uuid.uuid4().hex[:4]}", is_private=False)
    await room_repository.update_archived(db_session, arch_room.id, is_archived=True)
    await db_session.commit()

    t_free = create_access_token(subject=str(free_user.id))
    t_paid = create_access_token(subject=str(paid_user.id))
    t_admin = create_access_token(subject=str(admin_user.id))

    return {
        "free_user": free_user,
        "free_headers": {"Authorization": f"Bearer {t_free}"},
        "paid_user": paid_user,
        "paid_headers": {"Authorization": f"Bearer {t_paid}"},
        "admin_user": admin_user,
        "admin_headers": {"Authorization": f"Bearer {t_admin}"},
        "pub_room": pub_room,
        "priv_room": priv_room,
        "arch_room": arch_room,
    }


@pytest.mark.asyncio
async def test_public_room_join_and_leave_flow(client: AsyncClient, join_policy_users: dict):
    """
    Test joining and leaving a public room via REST API.
    """
    free_headers = join_policy_users["free_headers"]
    pub_room = join_policy_users["pub_room"]
    free_user = join_policy_users["free_user"]

    # 1. Join public room -> 200 OK
    join_resp = await client.post(
        f"/api/v1/rooms/{pub_room.id}/join",
        headers=free_headers,
    )
    assert join_resp.status_code == 200
    j_data = join_resp.json()
    assert j_data["user_id"] == str(free_user.id)
    assert j_data["room_id"] == str(pub_room.id)

    # 2. List members -> User present
    members_resp = await client.get(
        f"/api/v1/rooms/{pub_room.id}/members",
        headers=free_headers,
    )
    assert members_resp.status_code == 200
    m_data = members_resp.json()
    assert m_data["total"] >= 1
    assert any(m["user_id"] == str(free_user.id) for m in m_data["items"])

    # 3. Leave room -> 200 OK
    leave_resp = await client.delete(
        f"/api/v1/rooms/{pub_room.id}/leave",
        headers=free_headers,
    )
    assert leave_resp.status_code == 200
    assert leave_resp.json()["removed_at"] is not None


@pytest.mark.asyncio
async def test_private_room_subscription_paywall_enforcement(
    client: AsyncClient, join_policy_users: dict
):
    """
    Test private room subscription paywall (denied 403 for non-subscribers, allowed for subscribers and admins).
    """
    free_headers = join_policy_users["free_headers"]
    paid_headers = join_policy_users["paid_headers"]
    admin_headers = join_policy_users["admin_headers"]
    priv_room = join_policy_users["priv_room"]

    # 1. Free user (no subscription) joins private room -> Fails 403
    free_resp = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=free_headers,
    )
    assert free_resp.status_code == 403
    assert "subscription is required" in free_resp.json()["error"]["message"].lower()

    # 2. Paid user (active subscription) joins private room -> 200 OK
    paid_resp = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=paid_headers,
    )
    assert paid_resp.status_code == 200
    assert paid_resp.json()["user_id"] == str(join_policy_users["paid_user"].id)

    # 3. Admin user (no subscription) joins private room -> 200 OK (Admin bypass)
    admin_resp = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=admin_headers,
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["user_id"] == str(join_policy_users["admin_user"].id)


@pytest.mark.asyncio
async def test_join_archived_room_rejection(client: AsyncClient, join_policy_users: dict):
    """
    Test joining an archived room returns 400 Bad Request.
    """
    free_headers = join_policy_users["free_headers"]
    arch_room = join_policy_users["arch_room"]

    resp = await client.post(
        f"/api/v1/rooms/{arch_room.id}/join",
        headers=free_headers,
    )
    assert resp.status_code == 400
    assert "archived room" in resp.json()["error"]["message"].lower()
