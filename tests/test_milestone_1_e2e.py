"""
Milestone 1 End-to-End Integration Test Suite.

Verifies the integrated social follow system across all layers built in Tasks 1.1-1.5:
  - Database table & migration constraints
  - FollowRepository DAO queries
  - FollowService authorization matrix & DM permissions
  - FastAPI REST API endpoints
  - Account discovery PII privacy protection
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.services.follow_service import follow_service


@pytest_asyncio.fixture
async def e2e_users(db_session: AsyncSession):
    """Fixture creating user, writer, and admin accounts with JWT headers."""
    u1 = User(
        email=f"e2e_u1_{uuid.uuid4()}@ex.com",
        username=f"e2e_u1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    w1 = User(
        email=f"e2e_w1_{uuid.uuid4()}@ex.com",
        username=f"e2e_w1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.WRITER,
        is_active=True,
    )
    a1 = User(
        email=f"e2e_a1_{uuid.uuid4()}@ex.com",
        username=f"e2e_a1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u1, w1, a1])
    await db_session.commit()

    t1 = create_access_token(subject=str(u1.id))
    t_w1 = create_access_token(subject=str(w1.id))
    t_admin = create_access_token(subject=str(a1.id))

    return {
        "user": u1,
        "writer": w1,
        "admin": a1,
        "h_user": {"Authorization": f"Bearer {t1}"},
        "h_writer": {"Authorization": f"Bearer {t_w1}"},
        "h_admin": {"Authorization": f"Bearer {t_admin}"},
    }


@pytest.mark.asyncio
async def test_e2e_follow_and_dm_permission_lifecycle(client: AsyncClient, db_session: AsyncSession, e2e_users):
    u1, w1, h1 = e2e_users["user"], e2e_users["writer"], e2e_users["h_user"]

    # 1. Before follow -> DM permission must be False
    assert await follow_service.can_send_dm(db_session, u1.id, w1.id) is False

    # 2. HTTP POST /api/v1/follows -> Follow writer
    res = await client.post("/api/v1/follows", json={"target_user_id": str(w1.id)}, headers=h1)
    assert res.status_code == 201
    data = res.json()
    assert data["follower_id"] == str(u1.id)
    assert data["target_id"] == str(w1.id)

    # 3. After follow -> DM permission must be True for both participants
    assert await follow_service.can_send_dm(db_session, u1.id, w1.id) is True
    assert await follow_service.can_send_dm(db_session, w1.id, u1.id) is True

    # 4. HTTP DELETE /api/v1/follows/{id} -> Unfollow writer
    res = await client.delete(f"/api/v1/follows/{w1.id}", headers=h1)
    assert res.status_code == 200

    # 5. After unfollow -> DM permission revoked
    assert await follow_service.can_send_dm(db_session, u1.id, w1.id) is False


@pytest.mark.asyncio
async def test_e2e_self_follow_and_admin_guards(client: AsyncClient, e2e_users):
    u1, a1, h1, h_admin = e2e_users["user"], e2e_users["admin"], e2e_users["h_user"], e2e_users["h_admin"]

    # Self-follow attempt -> HTTP 400
    res = await client.post("/api/v1/follows", json={"target_user_id": str(u1.id)}, headers=h1)
    assert res.status_code == 400

    # Admin initiates follow -> HTTP 403
    res = await client.post("/api/v1/follows", json={"target_user_id": str(u1.id)}, headers=h_admin)
    assert res.status_code == 403

    # User follows Admin -> HTTP 403
    res = await client.post("/api/v1/follows", json={"target_user_id": str(a1.id)}, headers=h1)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_e2e_discovery_privacy_protection(client: AsyncClient, e2e_users):
    h1 = e2e_users["h_user"]
    res = await client.get("/api/v1/users/discover", headers=h1)
    assert res.status_code == 200
    items = res.json()["items"]
    for item in items:
        assert "email" not in item
        assert "hashed_password" not in item
        assert "stripe_customer_id" not in item
