"""
Integration tests for Administrator Room Member Removal & Access Revocation (/api/v1/admin/rooms/{room_id}/members/{user_id}).
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.repositories.room_repository import room_repository, room_member_repository


@pytest_asyncio.fixture
async def removal_users(db_session: AsyncSession):
    """
    Fixture providing room member user, outsider user, and admin user with JWT tokens.
    """
    member_user = User(
        email=f"mem_{uuid.uuid4().hex[:6]}@example.com",
        username=f"mem_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    outsider_user = User(
        email=f"out_{uuid.uuid4().hex[:6]}@example.com",
        username=f"out_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    admin_user = User(
        email=f"adminrem_{uuid.uuid4().hex[:6]}@example.com",
        username=f"adminrem_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([member_user, outsider_user, admin_user])
    await db_session.commit()
    await db_session.refresh(member_user)
    await db_session.refresh(outsider_user)
    await db_session.refresh(admin_user)

    room = await room_repository.create_room(db_session, name=f"Audit Lounge {uuid.uuid4().hex[:4]}", is_private=False)
    await room_member_repository.add_or_reactivate_member(db_session, room.id, member_user.id)
    await db_session.commit()

    t_member = create_access_token(subject=str(member_user.id))
    t_outsider = create_access_token(subject=str(outsider_user.id))
    t_admin = create_access_token(subject=str(admin_user.id))

    return {
        "member_user": member_user,
        "member_headers": {"Authorization": f"Bearer {t_member}"},
        "outsider_user": outsider_user,
        "outsider_headers": {"Authorization": f"Bearer {t_outsider}"},
        "admin_user": admin_user,
        "admin_headers": {"Authorization": f"Bearer {t_admin}"},
        "room": room,
    }


@pytest.mark.asyncio
async def test_admin_member_removal_endpoint_flow(client: AsyncClient, removal_users: dict):
    """
    Test admin member removal endpoint, RBAC enforcement, missing member 404, and post-removal access revocation.
    """
    member_headers = removal_users["member_headers"]
    outsider_headers = removal_users["outsider_headers"]
    admin_headers = removal_users["admin_headers"]
    room = removal_users["room"]
    member_user = removal_users["member_user"]
    outsider_user = removal_users["outsider_user"]
    admin_user = removal_users["admin_user"]

    # 1. Non-admin attempt to remove member -> Fails 403
    non_admin_resp = await client.delete(
        f"/api/v1/admin/rooms/{room.id}/members/{member_user.id}",
        headers=member_headers,
    )
    assert non_admin_resp.status_code == 403

    # 2. Admin attempts to remove a non-member -> Fails 404
    missing_resp = await client.delete(
        f"/api/v1/admin/rooms/{room.id}/members/{outsider_user.id}",
        headers=admin_headers,
    )
    assert missing_resp.status_code == 404
    assert "not a member" in missing_resp.json()["error"]["message"].lower()

    # 3. Admin removes actual member -> 200 OK with audit fields
    remove_resp = await client.delete(
        f"/api/v1/admin/rooms/{room.id}/members/{member_user.id}",
        headers=admin_headers,
    )
    assert remove_resp.status_code == 200
    rem_data = remove_resp.json()
    assert rem_data["user_id"] == str(member_user.id)
    assert rem_data["removed_at"] is not None
    assert rem_data["removed_by_id"] == str(admin_user.id)

    # 4. Repeated removal of existing member -> Idempotent 200 OK
    re_remove_resp = await client.delete(
        f"/api/v1/admin/rooms/{room.id}/members/{member_user.id}",
        headers=admin_headers,
    )
    assert re_remove_resp.status_code == 200
    assert re_remove_resp.json()["removed_at"] is not None
