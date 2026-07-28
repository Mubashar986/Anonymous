"""
Integration tests for Follow and Discovery REST API Endpoints (/api/v1/follows & /api/v1/users/discover).
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def api_users(db_session: AsyncSession):
    """Fixture providing created users and valid JWT headers."""
    u1 = User(
        email=f"api_u1_{uuid.uuid4()}@ex.com",
        username=f"api_u1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"api_u2_{uuid.uuid4()}@ex.com",
        username=f"api_u2_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    a1 = User(
        email=f"api_a1_{uuid.uuid4()}@ex.com",
        username=f"api_a1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u1, u2, a1])
    await db_session.commit()

    t1 = create_access_token(subject=str(u1.id))
    t2 = create_access_token(subject=str(u2.id))
    t_admin = create_access_token(subject=str(a1.id))

    return {
        "u1": u1,
        "u2": u2,
        "admin": a1,
        "h1": {"Authorization": f"Bearer {t1}"},
        "h2": {"Authorization": f"Bearer {t2}"},
        "h_admin": {"Authorization": f"Bearer {t_admin}"},
    }


@pytest.mark.asyncio
async def test_follow_api_flow(client: AsyncClient, api_users):
    u1, u2, h1, h2 = api_users["u1"], api_users["u2"], api_users["h1"], api_users["h2"]

    # 1. POST /api/v1/follows -> Success (201 Created)
    res = await client.post("/api/v1/follows", json={"target_user_id": str(u2.id)}, headers=h1)
    assert res.status_code == 201
    data = res.json()
    assert data["follower_id"] == str(u1.id)
    assert data["target_id"] == str(u2.id)

    # 2. GET /api/v1/follows/following -> u1 follows u2
    res = await client.get("/api/v1/follows/following", headers=h1)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(u2.id)

    # 3. GET /api/v1/follows/followers -> u2 has follower u1
    res = await client.get("/api/v1/follows/followers", headers=h2)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(u1.id)

    # 4. DELETE /api/v1/follows/{target_id} -> Unfollow (200 OK)
    res = await client.delete(f"/api/v1/follows/{u2.id}", headers=h1)
    assert res.status_code == 200

    # 5. Verify following list is now empty
    res = await client.get("/api/v1/follows/following", headers=h1)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0


@pytest.mark.asyncio
async def test_discover_users_api(client: AsyncClient, api_users):
    u2, h1 = api_users["u2"], api_users["h1"]
    res = await client.get("/api/v1/users/discover", headers=h1)
    assert res.status_code == 200
    items = res.json()["items"]
    # Admin (a1) and self (u1) omitted; u2 present
    assert any(item["id"] == str(u2.id) for item in items)
    # Confirm email is NOT in response item payload (security test)
    for item in items:
        assert "email" not in item
        assert "hashed_password" not in item
