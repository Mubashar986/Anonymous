"""
Pytest integration tests for Conversation and Message REST API endpoints.
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
async def api_chat_users(db_session: AsyncSession):
    u1 = User(email=f"api_c1_{uuid.uuid4()}@ex.com", username=f"api_c1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"api_c2_{uuid.uuid4()}@ex.com", username=f"api_c2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u3 = User(email=f"api_c3_{uuid.uuid4()}@ex.com", username=f"api_c3_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2, u3])
    await db_session.commit()

    await follow_repository.create(db_session, u1.id, u2.id)

    t1 = create_access_token(subject=str(u1.id))
    t3 = create_access_token(subject=str(u3.id))

    return u1, u2, u3, {"Authorization": f"Bearer {t1}"}, {"Authorization": f"Bearer {t3}"}


@pytest.mark.asyncio
async def test_conversation_api_flow(client: AsyncClient, api_chat_users):
    u1, u2, u3, h1, h3 = api_chat_users

    # 1. Start conversation u1 -> u2 (Followed -> 201 Created)
    res = await client.post("/api/v1/conversations", json={"target_user_id": str(u2.id)}, headers=h1)
    assert res.status_code == 201
    conv_id = res.json()["id"]

    # 2. List conversations for u1 -> 200 OK
    res = await client.get("/api/v1/conversations", headers=h1)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1

    # 3. Send message over REST -> 201 Created
    client_msg_id = str(uuid.uuid4())
    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"client_msg_id": client_msg_id, "text": "Hello REST!"},
        headers=h1,
    )
    assert res.status_code == 201
    assert res.json()["text"] == "Hello REST!"

    # 4. Fetch history for u1 -> 200 OK
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h1)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1

    # 5. Outsider u3 attempts to fetch history -> 403 Forbidden
    res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=h3)
    assert res.status_code == 403
