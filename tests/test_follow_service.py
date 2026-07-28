"""
Unit & Integration tests for FollowService and FollowRepository.
"""

import uuid
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.follow_service import follow_service
from app.repositories.follow_repository import follow_repository
from app.repositories.user_repository import user_repository


@pytest_asyncio.fixture
async def sample_users(db_session: AsyncSession):
    """Fixture creating user, writer, and admin accounts for testing."""
    u1 = User(
        email=f"user1_{uuid.uuid4()}@ex.com",
        username=f"u1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"user2_{uuid.uuid4()}@ex.com",
        username=f"u2_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    w1 = User(
        email=f"writer1_{uuid.uuid4()}@ex.com",
        username=f"w1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.WRITER,
        is_active=True,
    )
    a1 = User(
        email=f"admin1_{uuid.uuid4()}@ex.com",
        username=f"a1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u1, u2, w1, a1])
    await db_session.commit()
    return {"user1": u1, "user2": u2, "writer": w1, "admin": a1}


@pytest.mark.asyncio
async def test_follow_user_success(db_session: AsyncSession, sample_users):
    u1, w1 = sample_users["user1"], sample_users["writer"]
    follow = await follow_service.follow_user(db_session, current_user=u1, target_user_id=w1.id)
    assert follow.follower_id == u1.id
    assert follow.target_id == w1.id


@pytest.mark.asyncio
async def test_follow_self_forbidden(db_session: AsyncSession, sample_users):
    u1 = sample_users["user1"]
    with pytest.raises(HTTPException) as exc_info:
        await follow_service.follow_user(db_session, current_user=u1, target_user_id=u1.id)
    assert exc_info.value.status_code == 400
    assert "cannot follow yourself" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_admin_cannot_follow(db_session: AsyncSession, sample_users):
    a1, u1 = sample_users["admin"], sample_users["user1"]
    with pytest.raises(HTTPException) as exc_info:
        await follow_service.follow_user(db_session, current_user=a1, target_user_id=u1.id)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cannot_follow_admin(db_session: AsyncSession, sample_users):
    u1, a1 = sample_users["user1"], sample_users["admin"]
    with pytest.raises(HTTPException) as exc_info:
        await follow_service.follow_user(db_session, current_user=u1, target_user_id=a1.id)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_follow_rejected(db_session: AsyncSession, sample_users):
    u1, u2 = sample_users["user1"], sample_users["user2"]
    await follow_service.follow_user(db_session, current_user=u1, target_user_id=u2.id)
    with pytest.raises(HTTPException) as exc_info:
        await follow_service.follow_user(db_session, current_user=u1, target_user_id=u2.id)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_can_send_dm_authorization(db_session: AsyncSession, sample_users):
    u1, u2 = sample_users["user1"], sample_users["user2"]
    # Before follow
    assert await follow_service.can_send_dm(db_session, u1.id, u2.id) is False
    # After u1 follows u2
    await follow_service.follow_user(db_session, current_user=u1, target_user_id=u2.id)
    assert await follow_service.can_send_dm(db_session, u1.id, u2.id) is True
    assert await follow_service.can_send_dm(db_session, u2.id, u1.id) is True  # Either can reply
    # After unfollow
    await follow_service.unfollow_user(db_session, current_user=u1, target_user_id=u2.id)
    assert await follow_service.can_send_dm(db_session, u1.id, u2.id) is False
