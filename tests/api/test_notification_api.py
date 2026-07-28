"""
Integration tests for Notification REST API Endpoints and Ownership Boundaries.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.notification import Notification


@pytest_asyncio.fixture
async def api_users(db_session: AsyncSession):
    """Fixture providing created users and valid JWT headers."""
    u1 = User(
        email=f"notif_u1_{uuid.uuid4()}@ex.com",
        username=f"notif_u1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"notif_u2_{uuid.uuid4()}@ex.com",
        username=f"notif_u2_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add_all([u1, u2])
    await db_session.commit()

    t1 = create_access_token(subject=str(u1.id))
    t2 = create_access_token(subject=str(u2.id))

    return {
        "u1": u1,
        "u2": u2,
        "h1": {"Authorization": f"Bearer {t1}"},
        "h2": {"Authorization": f"Bearer {t2}"},
    }


@pytest.mark.asyncio
async def test_notifications_unauthenticated(client: AsyncClient):
    """Assert unauthenticated requests return 401."""
    response = await client.get("/api/v1/notifications/unread-count")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_notifications_empty_list(client: AsyncClient, api_users: dict):
    """Assert new user has 0 notifications and 0 unread count."""
    h1 = api_users["h1"]
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert count_resp.status_code == 200
    assert count_resp.json()["unread_count"] == 0

    list_resp = await client.get("/api/v1/notifications", headers=h1)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_notifications_list_and_mark_read(
    client: AsyncClient,
    api_users: dict,
    db_session: AsyncSession,
):
    """Assert listing notifications, marking single read, and bulk marking read."""
    u1, h1 = api_users["u1"], api_users["h1"]

    # Seed 2 notifications for u1
    notif1 = Notification(
        recipient_id=u1.id,
        event_type="new_follower",
        payload={"actor_username": "bob", "navigation_target": "profile"},
        idempotency_key=f"new_follower:{uuid.uuid4()}:{u1.id}:{u1.id}",
        is_read=False,
    )
    notif2 = Notification(
        recipient_id=u1.id,
        event_type="blog_approved",
        payload={"title": "My Post", "navigation_target": "blog_detail"},
        idempotency_key=f"blog_approved:{uuid.uuid4()}:{u1.id}:{uuid.uuid4()}",
        is_read=False,
    )
    db_session.add_all([notif1, notif2])
    await db_session.commit()

    # Unread count should be 2
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert count_resp.json()["unread_count"] == 2

    # List items
    list_resp = await client.get("/api/v1/notifications", headers=h1)
    data = list_resp.json()
    assert data["total"] == 2
    assert data["unread_count"] == 2
    assert len(data["items"]) == 2

    # Mark single read
    read_resp = await client.patch(
        f"/api/v1/notifications/{notif1.id}/read",
        headers=h1,
    )
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # Check unread count is now 1
    count_resp2 = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert count_resp2.json()["unread_count"] == 1

    # Bulk mark all read
    bulk_resp = await client.post("/api/v1/notifications/read-all", headers=h1)
    assert bulk_resp.status_code == 200
    assert bulk_resp.json()["updated_count"] == 1

    # Final unread count should be 0
    count_resp3 = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert count_resp3.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notifications_ownership_isolation_returns_404(
    client: AsyncClient,
    api_users: dict,
    db_session: AsyncSession,
):
    """Assert User A (h1) cannot read or mark User B's (u2) notification (returns 404 Not Found)."""
    u1, u2, h1 = api_users["u1"], api_users["u2"], api_users["h1"]

    # Seed notification for u2 (User B)
    notif_b = Notification(
        recipient_id=u2.id,
        event_type="new_follower",
        payload={"actor_username": "charlie", "navigation_target": "profile"},
        idempotency_key=f"new_follower:{uuid.uuid4()}:{u2.id}:{u2.id}",
        is_read=False,
    )
    db_session.add(notif_b)
    await db_session.commit()

    # User A (h1) attempts to mark User B's notification read
    patch_resp = await client.patch(
        f"/api/v1/notifications/{notif_b.id}/read",
        headers=h1,
    )
    # Must return 404 Not Found to prevent ID enumeration
    assert patch_resp.status_code == 404
    assert patch_resp.json()["error"]["message"] == "Notification not found"

    # User A listing notifications should see 0 items
    list_resp = await client.get("/api/v1/notifications", headers=h1)
    assert list_resp.json()["total"] == 0
