"""
Integration tests asserting domain actions emit recipient notification records.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.models.blog import Blog, BlogStatus
from app.models.room import RoomRequest, RoomRequestStatus
from app.services.follow_service import follow_service
from app.services.conversation_service import conversation_service
from app.services.blog_service import blog_service
from app.services.room_service import room_service
from app.services.policy_service import policy_evaluator
from app.schemas.permission import CapabilityEnum, OverrideEffectEnum
from app.schemas.blog import BlogApprove


@pytest_asyncio.fixture
async def domain_users(db_session: AsyncSession):
    """Fixture providing user, writer, and admin accounts."""
    u1 = User(
        email=f"dom_u1_{uuid.uuid4()}@ex.com",
        username=f"dom_u1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"dom_u2_{uuid.uuid4()}@ex.com",
        username=f"dom_u2_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    w1 = User(
        email=f"dom_w1_{uuid.uuid4()}@ex.com",
        username=f"dom_w1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.WRITER,
        is_active=True,
    )
    admin = User(
        email=f"dom_admin_{uuid.uuid4()}@ex.com",
        username=f"dom_admin_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u1, u2, w1, admin])
    await db_session.commit()

    return {"u1": u1, "u2": u2, "w1": w1, "admin": admin}


@pytest.mark.asyncio
async def test_follow_emits_new_follower_notification(
    db_session: AsyncSession, domain_users: dict
):
    """Assert following a user creates a NEW_FOLLOWER notification for target user."""
    u1, u2 = domain_users["u1"], domain_users["u2"]

    await follow_service.follow_user(db_session, current_user=u1, target_user_id=u2.id)

    stmt = select(Notification).where(
        Notification.recipient_id == u2.id,
        Notification.event_type == "new_follower",
    )
    res = await db_session.execute(stmt)
    notifs = res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].actor_id == u1.id
    assert notifs[0].payload["actor_username"] == u1.username


@pytest.mark.asyncio
async def test_direct_message_emits_notification(
    db_session: AsyncSession, domain_users: dict
):
    """Assert sending a DM creates a NEW_DIRECT_MESSAGE notification for recipient."""
    u1, u2 = domain_users["u1"], domain_users["u2"]

    # Establish follow relationship required for DM
    await follow_service.follow_user(db_session, current_user=u1, target_user_id=u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)

    await conversation_service.send_message(
        db_session,
        current_user=u1,
        conversation_id=conv.id,
        client_msg_id=uuid.uuid4(),
        text="Hello world!",
    )

    stmt = select(Notification).where(
        Notification.recipient_id == u2.id,
        Notification.event_type == "new_direct_message",
    )
    res = await db_session.execute(stmt)
    notifs = res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].actor_id == u1.id


@pytest.mark.asyncio
async def test_blog_approval_emits_notification(
    db_session: AsyncSession, domain_users: dict
):
    """Assert admin approving a blog creates a BLOG_APPROVED notification for author."""
    w1, admin = domain_users["w1"], domain_users["admin"]

    blog = Blog(
        title="Test Blog Post",
        content="Testing notification creation.",
        author_id=w1.id,
        status=BlogStatus.PENDING,
    )
    db_session.add(blog)
    await db_session.commit()

    await blog_service.approve_blog(
        db_session,
        current_user=admin,
        blog_id=blog.id,
        approve_in=BlogApprove(status=BlogStatus.APPROVED),
    )

    stmt = select(Notification).where(
        Notification.recipient_id == w1.id,
        Notification.event_type == "blog_approved",
    )
    res = await db_session.execute(stmt)
    notifs = res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].actor_id == admin.id
    assert "approved" in notifs[0].payload["summary_text"]


@pytest.mark.asyncio
async def test_permission_override_emits_notification(
    db_session: AsyncSession, domain_users: dict
):
    """Assert setting permission override creates a PERMISSION_OVERRIDE_CHANGED notification."""
    u1, admin = domain_users["u1"], domain_users["admin"]

    await policy_evaluator.set_user_override(
        db=db_session,
        actor=admin,
        target_user=u1,
        capability=CapabilityEnum.CAN_CREATE_ROOM,
        effect=OverrideEffectEnum.ALLOW,
        reason="VIP user promotion",
    )

    stmt = select(Notification).where(
        Notification.recipient_id == u1.id,
        Notification.event_type == "permission_override_changed",
    )
    res = await db_session.execute(stmt)
    notifs = res.scalars().all()
    assert len(notifs) == 1
    assert notifs[0].actor_id == admin.id
    assert "can_create_room" in notifs[0].payload["summary_text"]
