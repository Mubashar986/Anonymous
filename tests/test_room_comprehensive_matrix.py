"""
Comprehensive Matrix Integration Tests for Community Rooms, Access Entitlement Policies, and Administrative Workflows.
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
from app.repositories.room_repository import room_repository, room_member_repository


@pytest_asyncio.fixture
async def matrix_environment(db_session: AsyncSession):
    """
    Fixture creating a full matrix environment:
    - User Roles: Regular User, Writer, Admin
    - Subscription States: Active, Canceled, Expired, None
    - Room Visibilities: Public, Private
    """
    # 1. Users
    u_active = User(
        email=f"u_act_{uuid.uuid4().hex[:6]}@example.com",
        username=f"u_act_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    u_canceled = User(
        email=f"u_can_{uuid.uuid4().hex[:6]}@example.com",
        username=f"u_can_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    u_expired = User(
        email=f"u_exp_{uuid.uuid4().hex[:6]}@example.com",
        username=f"u_exp_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    u_none = User(
        email=f"u_non_{uuid.uuid4().hex[:6]}@example.com",
        username=f"u_non_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    w_user = User(
        email=f"w_usr_{uuid.uuid4().hex[:6]}@example.com",
        username=f"w_usr_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.WRITER,
        is_active=True,
    )
    a_user = User(
        email=f"a_usr_{uuid.uuid4().hex[:6]}@example.com",
        username=f"a_usr_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u_active, u_canceled, u_expired, u_none, w_user, a_user])
    await db_session.commit()

    # 2. Subscriptions
    sub_active = Subscription(
        user_id=u_active.id,
        stripe_customer_id="cus_act",
        stripe_subscription_id="sub_act",
        stripe_price_id="price_vip",
        status="active",
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    sub_canceled = Subscription(
        user_id=u_canceled.id,
        stripe_customer_id="cus_can",
        stripe_subscription_id="sub_can",
        stripe_price_id="price_vip",
        status="canceled",
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    sub_expired = Subscription(
        user_id=u_expired.id,
        stripe_customer_id="cus_exp",
        stripe_subscription_id="sub_exp",
        stripe_price_id="price_vip",
        status="active",
        current_period_end=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add_all([sub_active, sub_canceled, sub_expired])
    await db_session.commit()

    # 3. Rooms
    pub_room = await room_repository.create_room(db_session, name=f"Matrix Public {uuid.uuid4().hex[:4]}", is_private=False)
    priv_room = await room_repository.create_room(db_session, name=f"Matrix Private {uuid.uuid4().hex[:4]}", is_private=True)
    await db_session.commit()

    # 4. JWT Headers
    return {
        "u_active": u_active,
        "h_active": {"Authorization": f"Bearer {create_access_token(subject=str(u_active.id))}"},
        "u_canceled": u_canceled,
        "h_canceled": {"Authorization": f"Bearer {create_access_token(subject=str(u_canceled.id))}"},
        "u_expired": u_expired,
        "h_expired": {"Authorization": f"Bearer {create_access_token(subject=str(u_expired.id))}"},
        "u_none": u_none,
        "h_none": {"Authorization": f"Bearer {create_access_token(subject=str(u_none.id))}"},
        "w_user": w_user,
        "h_writer": {"Authorization": f"Bearer {create_access_token(subject=str(w_user.id))}"},
        "a_user": a_user,
        "h_admin": {"Authorization": f"Bearer {create_access_token(subject=str(a_user.id))}"},
        "pub_room": pub_room,
        "priv_room": priv_room,
    }


@pytest.mark.asyncio
async def test_matrix_room_request_lifecycle_and_rbac(
    client: AsyncClient, matrix_environment: dict
):
    """
    Matrix Test 1: Room request lifecycle, admin approval with final_name, admin rejection, double-approval block.
    """
    h_none = matrix_environment["h_none"]
    h_writer = matrix_environment["h_writer"]
    h_admin = matrix_environment["h_admin"]
    u_none = matrix_environment["u_none"]

    # 1. User submits room request -> 201 Created
    req1_resp = await client.post(
        "/api/v1/rooms/requests",
        json={"name": "Cloud Native Architecture", "is_private": False},
        headers=h_none,
    )
    assert req1_resp.status_code == 201
    req1_id = req1_resp.json()["id"]

    # 2. Non-admin approval attempt -> Fails 403
    forbidden_app = await client.post(
        f"/api/v1/admin/rooms/requests/{req1_id}/approve",
        json={"final_name": "Cloud Native Hub"},
        headers=h_writer,
    )
    assert forbidden_app.status_code == 403

    # 3. Admin approves request -> 200 OK
    app_resp = await client.post(
        f"/api/v1/admin/rooms/requests/{req1_id}/approve",
        json={"final_name": "Cloud Native Hub"},
        headers=h_admin,
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["request"]["status"] == "approved"
    assert app_resp.json()["room"]["name"] == "Cloud Native Hub"

    # 4. Double-approval attempt -> Fails 400
    double_app = await client.post(
        f"/api/v1/admin/rooms/requests/{req1_id}/approve",
        headers=h_admin,
    )
    assert double_app.status_code == 400

    # 5. User submits 2nd request for rejection test
    req2_resp = await client.post(
        "/api/v1/rooms/requests",
        json={"name": "Spam Room Name", "is_private": False},
        headers=h_none,
    )
    req2_id = req2_resp.json()["id"]

    # 6. Admin rejects 2nd request -> 200 OK
    rej_resp = await client.post(
        f"/api/v1/admin/rooms/requests/{req2_id}/reject",
        headers=h_admin,
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_matrix_subscription_states_paywall_enforcement(
    client: AsyncClient, matrix_environment: dict
):
    """
    Matrix Test 2: Private room paywall checks across active, canceled, expired, none, and admin bypass.
    """
    priv_room = matrix_environment["priv_room"]

    # 1. Active subscriber -> 200 OK
    r_act = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=matrix_environment["h_active"],
    )
    assert r_act.status_code == 200

    # 2. Canceled subscriber -> 403 Forbidden
    r_can = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=matrix_environment["h_canceled"],
    )
    assert r_can.status_code == 403

    # 3. Expired subscriber -> 403 Forbidden
    r_exp = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=matrix_environment["h_expired"],
    )
    assert r_exp.status_code == 403

    # 4. No subscription -> 403 Forbidden
    r_non = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=matrix_environment["h_none"],
    )
    assert r_non.status_code == 403

    # 5. Admin user (no subscription) -> 200 OK (Bypass)
    r_adm = await client.post(
        f"/api/v1/rooms/{priv_room.id}/join",
        headers=matrix_environment["h_admin"],
    )
    assert r_adm.status_code == 200


@pytest.mark.asyncio
async def test_matrix_archival_and_removal_access_revocation(
    client: AsyncClient, matrix_environment: dict
):
    """
    Matrix Test 3: Admin direct room creation, room archival lockout, and member removal.
    """
    h_admin = matrix_environment["h_admin"]
    h_active = matrix_environment["h_active"]
    u_active = matrix_environment["u_active"]

    # 1. Admin directly creates room -> 201 Created
    create_resp = await client.post(
        "/api/v1/admin/rooms",
        json={"name": "DevOps Guild", "is_private": False},
        headers=h_admin,
    )
    assert create_resp.status_code == 201
    room_id = create_resp.json()["id"]

    # 2. Active user joins room -> 200 OK
    join_resp = await client.post(
        f"/api/v1/rooms/{room_id}/join",
        headers=h_active,
    )
    assert join_resp.status_code == 200

    # 3. Admin archives room -> 200 OK
    arc_resp = await client.patch(
        f"/api/v1/admin/rooms/{room_id}/archive",
        headers=h_admin,
    )
    assert arc_resp.status_code == 200
    assert arc_resp.json()["is_archived"] is True

    # 4. Attempting join to archived room -> 400 Bad Request
    join_arc = await client.post(
        f"/api/v1/rooms/{room_id}/join",
        headers=matrix_environment["h_none"],
    )
    assert join_arc.status_code == 400

    # 5. Admin removes member from non-archived room
    pub_room = matrix_environment["pub_room"]
    await client.post(f"/api/v1/rooms/{pub_room.id}/join", headers=h_active)

    rem_resp = await client.delete(
        f"/api/v1/admin/rooms/{pub_room.id}/members/{u_active.id}",
        headers=h_admin,
    )
    assert rem_resp.status_code == 200
    assert rem_resp.json()["removed_at"] is not None
    assert rem_resp.json()["removed_by_id"] == str(matrix_environment["a_user"].id)
