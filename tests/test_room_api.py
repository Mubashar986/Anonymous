"""
Integration tests for Community Rooms and Room Request REST API endpoints.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.room import RoomRequestStatus
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def auth_tokens(db_session: AsyncSession):
    """
    Fixture providing authenticated user, writer, and admin tokens.
    """
    user = User(
        email=f"api_user_{uuid.uuid4().hex[:6]}@example.com",
        username=f"api_user_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
    )
    writer = User(
        email=f"api_writer_{uuid.uuid4().hex[:6]}@example.com",
        username=f"api_writer_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.WRITER,
        is_active=True,
    )
    admin = User(
        email=f"api_admin_{uuid.uuid4().hex[:6]}@example.com",
        username=f"api_admin_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user, writer, admin])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(writer)
    await db_session.refresh(admin)

    user_token = create_access_token(subject=str(user.id))
    writer_token = create_access_token(subject=str(writer.id))
    admin_token = create_access_token(subject=str(admin.id))

    return {
        "user": user,
        "user_headers": {"Authorization": f"Bearer {user_token}"},
        "writer": writer,
        "writer_headers": {"Authorization": f"Bearer {writer_token}"},
        "admin": admin,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
    }


@pytest.mark.asyncio
async def test_submit_room_request_endpoint(client: AsyncClient, auth_tokens: dict):
    """
    Test POST /api/v1/rooms/requests by user and writer.
    """
    resp = await client.post(
        "/api/v1/rooms/requests",
        json={"name": "Rust Enthusiasts", "is_private": False},
        headers=auth_tokens["user_headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Rust Enthusiasts"
    assert data["status"] == "pending"
    assert data["requester_id"] == str(auth_tokens["user"].id)

    me_resp = await client.get(
        "/api/v1/rooms/requests/me",
        headers=auth_tokens["user_headers"],
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["total"] >= 1
    assert me_data["items"][0]["name"] == "Rust Enthusiasts"


@pytest.mark.asyncio
async def test_admin_approve_room_request_with_name_override(
    client: AsyncClient, auth_tokens: dict
):
    """
    Test admin approval endpoint POST /api/v1/admin/rooms/requests/{id}/approve with optional final_name override.
    """
    req_resp = await client.post(
        "/api/v1/rooms/requests",
        json={"name": "Golang Hub", "is_private": False},
        headers=auth_tokens["writer_headers"],
    )
    req_id = req_resp.json()["id"]

    forbidden_resp = await client.post(
        f"/api/v1/admin/rooms/requests/{req_id}/approve",
        json={"final_name": "Golang Master Class"},
        headers=auth_tokens["user_headers"],
    )
    assert forbidden_resp.status_code == 403

    approve_resp = await client.post(
        f"/api/v1/admin/rooms/requests/{req_id}/approve",
        json={"final_name": "Golang Master Class"},
        headers=auth_tokens["admin_headers"],
    )
    assert approve_resp.status_code == 200
    app_data = approve_resp.json()
    assert app_data["request"]["status"] == "approved"
    assert app_data["room"]["name"] == "Golang Master Class"

    rooms_resp = await client.get(
        "/api/v1/rooms",
        headers=auth_tokens["user_headers"],
    )
    assert rooms_resp.status_code == 200
    room_names = [r["name"] for r in rooms_resp.json()["items"]]
    assert "Golang Master Class" in room_names


@pytest.mark.asyncio
async def test_admin_reject_room_request_endpoint(client: AsyncClient, auth_tokens: dict):
    """
    Test POST /api/v1/admin/rooms/requests/{id}/reject by admin and non-admin RBAC check.
    """
    req_resp = await client.post(
        "/api/v1/rooms/requests",
        json={"name": "Invalid Room", "is_private": False},
        headers=auth_tokens["user_headers"],
    )
    req_id = req_resp.json()["id"]

    reject_resp = await client.post(
        f"/api/v1/admin/rooms/requests/{req_id}/reject",
        headers=auth_tokens["admin_headers"],
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_admin_direct_room_creation_and_archival(
    client: AsyncClient, auth_tokens: dict
):
    """
    Test POST /api/v1/admin/rooms and PATCH /api/v1/admin/rooms/{id}/archive.
    """
    create_resp = await client.post(
        "/api/v1/admin/rooms",
        json={"name": "Executive Lounge", "is_private": True},
        headers=auth_tokens["admin_headers"],
    )
    assert create_resp.status_code == 201
    room_id = create_resp.json()["id"]
    assert create_resp.json()["is_private"] is True

    archive_resp = await client.patch(
        f"/api/v1/admin/rooms/{room_id}/archive",
        headers=auth_tokens["admin_headers"],
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["is_archived"] is True
