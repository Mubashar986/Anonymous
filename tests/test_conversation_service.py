"""
Pytest unit tests for ConversationService policy and authorization logic.
"""

import uuid
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.follow_repository import follow_repository
from app.services.conversation_service import conversation_service


@pytest_asyncio.fixture
async def cs_users(db_session: AsyncSession):
    u1 = User(email=f"cs1_{uuid.uuid4()}@ex.com", username=f"cs1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"cs2_{uuid.uuid4()}@ex.com", username=f"cs2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    a1 = User(email=f"csa_{uuid.uuid4()}@ex.com", username=f"csa_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.ADMIN, is_active=True)
    db_session.add_all([u1, u2, a1])
    await db_session.commit()
    return u1, u2, a1


@pytest.mark.asyncio
async def test_start_conversation_requires_follow(db_session: AsyncSession, cs_users):
    u1, u2, _ = cs_users
    # Unfollowed -> HTTP 403
    with pytest.raises(HTTPException) as exc:
        await conversation_service.start_conversation(db_session, u1, u2.id)
    assert exc.value.status_code == 403

    # Follow u2 -> Success
    await follow_repository.create(db_session, u1.id, u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)
    assert conv.id is not None


@pytest.mark.asyncio
async def test_send_message_revoked_follow(db_session: AsyncSession, cs_users):
    u1, u2, _ = cs_users
    await follow_repository.create(db_session, u1.id, u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)

    # Send message while followed -> Success
    msg = await conversation_service.send_message(db_session, u1, conv.id, uuid.uuid4(), "Hello!")
    assert msg.text == "Hello!"

    # Unfollow -> Send message throws HTTP 403
    await follow_repository.delete(db_session, u1.id, u2.id)
    with pytest.raises(HTTPException) as exc:
        await conversation_service.send_message(db_session, u1, conv.id, uuid.uuid4(), "Still there?")
    assert exc.value.status_code == 403
