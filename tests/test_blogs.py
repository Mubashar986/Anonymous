"""
Integration tests for Blog Management API (Task 2).
Tests role-based permissions, blog approval workflows, and ownership rules.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.blog import Blog, BlogStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_writer_create_blog_pending(client: AsyncClient, db_session: AsyncSession):
    """
    Test writer creating a blog defaults to 'pending' status.
    """
    writer = User(
        email="writer1@example.com",
        username="writer1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(writer)
    await db_session.commit()

    token = create_access_token(subject=writer.id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"title": "My First Writer Blog", "content": "This is a great blog post content."}
    response = await client.post("/api/v1/blogs", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "pending"
    assert data["author_id"] == str(writer.id)


@pytest.mark.asyncio
async def test_user_cannot_see_pending_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user cannot see pending blogs in GET /api/v1/blogs.
    """
    writer = User(
        email="writer2@example.com",
        username="writer2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(writer)
    await db_session.commit()

    pending_blog = Blog(
        title="Pending Blog Post",
        content="Secret draft content.",
        status=BlogStatus.PENDING,
        author_id=writer.id,
    )
    db_session.add(pending_blog)
    await db_session.commit()

    # Standard User
    user = User(
        email="user1@example.com",
        username="user1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/blogs", headers=headers)
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 0


@pytest.mark.asyncio
async def test_admin_approve_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test admin approving a pending blog.
    """
    writer = User(
        email="writer3@example.com",
        username="writer3",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    admin = User(
        email="admin1@example.com",
        username="admin1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([writer, admin])
    await db_session.commit()

    pending_blog = Blog(
        title="Blog To Approve",
        content="Pending approval text.",
        status=BlogStatus.PENDING,
        author_id=writer.id,
    )
    db_session.add(pending_blog)
    await db_session.commit()

    admin_token = create_access_token(subject=admin.id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    approve_payload = {"status": "approved"}
    response = await client.patch(
        f"/api/v1/blogs/{pending_blog.id}/approve",
        json=approve_payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_user_can_see_approved_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user can see approved blogs.
    """
    writer = User(
        email="writer4@example.com",
        username="writer4",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    user = User(
        email="user2@example.com",
        username="user2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([writer, user])
    await db_session.commit()

    approved_blog = Blog(
        title="Approved Blog",
        content="Public article content.",
        status=BlogStatus.APPROVED,
        author_id=writer.id,
    )
    db_session.add(approved_blog)
    await db_session.commit()

    user_token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {user_token}"}

    response = await client.get("/api/v1/blogs", headers=headers)
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["title"] == "Approved Blog"


@pytest.mark.asyncio
async def test_writer_cannot_update_other_writer_blog(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Test writer 2 cannot update writer 1's blog (403 Forbidden).
    """
    writer1 = User(
        email="w1@example.com",
        username="w1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    writer2 = User(
        email="w2@example.com",
        username="w2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([writer1, writer2])
    await db_session.commit()

    blog = Blog(
        title="Writer 1 Blog",
        content="Original content",
        status=BlogStatus.APPROVED,
        author_id=writer1.id,
    )
    db_session.add(blog)
    await db_session.commit()

    writer2_token = create_access_token(subject=writer2.id)
    headers = {"Authorization": f"Bearer {writer2_token}"}

    response = await client.patch(
        f"/api/v1/blogs/{blog.id}",
        json={"title": "Hacked Title"},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_create_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user cannot create blogs (403 Forbidden).
    """
    user = User(
        email="user3@example.com",
        username="user3",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/blogs",
        json={"title": "User Attempt", "content": "User trying to post"},
        headers=headers,
    )
    assert response.status_code == 403
