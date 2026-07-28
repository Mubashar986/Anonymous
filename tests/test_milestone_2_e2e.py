"""
Milestone 2 End-to-End Integration Test Suite.

Verifies the durable one-to-one messaging system across all layers built in Tasks 2.1-2.5:
  - Database tables & migration (conversations, messages)
  - Repositories (ConversationRepository, MessageRepository)
  - ConversationService policy enforcement
  - REST API endpoints (/conversations, /conversations/{id}/messages)
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.repositories.follow_repository import follow_repository


@pytest_asyncio.fixture
async def m2_users(db_session: AsyncSession):
    u1 = User(email=f"m2_1_{uuid.uuid4()}@ex.com", username=f"m2_1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"m2_2_{uuid.uuid4()}@ex.com", username=f"m2_2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u3 = User(email=f"m2_3_{uuid.uuid4()}@ex.com", username=f"m2_3_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2, u3])
    await db_session.commit()

    await follow_repository.create(db_session, u1.id, u2.id)

    t1 = create_access_token(subject=str(u1.id))
    t2 = create_access_token(subject=str(u2.id))
    t3 = create_access_token(subject=str(u3.id))

    return {
        "u1": u1, "u2": u2, "u3": u3,
        "h1": {"Authorization": f"Bearer {t1}"},
        "h2": {"Authorization": f"Bearer {t2}"},
        "h3": {"Authorization": f"Bearer {t3}"},
    }


@pytest.mark.asyncio
async def test_e2e_full_messaging_lifecycle(client: AsyncClient, m2_users):
    u1, u2, h1, h2 = m2_users["u1"], m2_users["u2"], m2_users["h1"], m2_users["h2"]

    # 1. Start conversation (u1 -> u2) -> 201 Created
    res = await client.post("/api/v1/conversations", json={"target_user_id": str(u2.id)}, headers=h1)
    assert res.status_code == 201
    conv_id = res.json()["id"]

    # 2. Send message 1 from u1 over REST -> 201 Created
    msg1_client_id = str(uuid.uuid4())
    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"client_msg_id": msg1_client_id, "text": "Hello Bob!"},
        headers=h1,
    )
    assert res.status_code == 201
    assert res.json()["text"] == "Hello Bob!"

    # 3. Read history from u2's perspective -> 200 OK (contains 1 message)
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h2)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["text"] == "Hello Bob!"

    # 4. Reply message 2 from u2 -> 201 Created
    msg2_client_id = str(uuid.uuid4())
    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"client_msg_id": msg2_client_id, "text": "Hey Alice!"},
        headers=h2,
    )
    assert res.status_code == 201

    # 5. Read history from u1's perspective -> 200 OK (contains 2 messages in order)
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h1)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    assert items[0]["text"] == "Hello Bob!"
    assert items[1]["text"] == "Hey Alice!"


@pytest.mark.asyncio
async def test_e2e_messaging_revoked_follow_and_outsider_denial(client: AsyncClient, db_session: AsyncSession, m2_users):
    u1, u2, u3, h1, h3 = m2_users["u1"], m2_users["u2"], m2_users["u3"], m2_users["h1"], m2_users["h3"]

    # 1. Start conversation & send message
    res = await client.post("/api/v1/conversations", json={"target_user_id": str(u2.id)}, headers=h1)
    conv_id = res.json()["id"]
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"client_msg_id": str(uuid.uuid4()), "text": "Before unfollow"},
        headers=h1,
    )

    # 2. Outsider u3 attempts to fetch history -> 403 Forbidden
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h3)
    assert res.status_code == 403

    # 3. Unfollow target
    await follow_repository.delete(db_session, u1.id, u2.id)

    # 4. Attempt to send new message post-unfollow -> 403 Forbidden
    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"client_msg_id": str(uuid.uuid4()), "text": "Blocked message"},
        headers=h1,
    )
    assert res.status_code == 403

    # 5. Read retained history post-unfollow -> 200 OK (history retained!)
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h1)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1
    assert res.json()["items"][0]["text"] == "Before unfollow"
