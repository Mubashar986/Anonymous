"""
Pytest unit tests for ConversationRepository and MessageRepository.
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.conversation_repository import conversation_repository
from app.repositories.message_repository import message_repository


@pytest_asyncio.fixture
async def chat_users(db_session: AsyncSession):
    u1 = User(email=f"cu1_{uuid.uuid4()}@ex.com", username=f"cu1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"cu2_{uuid.uuid4()}@ex.com", username=f"cu2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2])
    await db_session.commit()
    return u1, u2


@pytest.mark.asyncio
async def test_get_or_create_conversation_order_invariant(db_session: AsyncSession, chat_users):
    u1, u2 = chat_users
    # Create with (u1, u2)
    c1 = await conversation_repository.get_or_create_for_pair(db_session, u1.id, u2.id)
    # Lookup with (u2, u1) -> must return same conversation
    c2 = await conversation_repository.get_or_create_for_pair(db_session, u2.id, u1.id)
    assert c1.id == c2.id
    assert await conversation_repository.is_participant(db_session, c1.id, u1.id) is True
    assert await conversation_repository.is_participant(db_session, c1.id, u2.id) is True


@pytest.mark.asyncio
async def test_message_idempotency_client_msg_id(db_session: AsyncSession, chat_users):
    u1, u2 = chat_users
    conv = await conversation_repository.get_or_create_for_pair(db_session, u1.id, u2.id)
    client_msg_id = uuid.uuid4()

    m1 = await message_repository.create(db_session, conv.id, u1.id, client_msg_id, "Hello!")
    # Repeat insert with same client_msg_id
    m2 = await message_repository.create(db_session, conv.id, u1.id, client_msg_id, "Hello!")
    assert m1.id == m2.id

    history = await message_repository.get_history(db_session, conv.id)
    assert len(history) == 1
    assert history[0].text == "Hello!"
