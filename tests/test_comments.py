"""
Integration tests for Comment Management API (Task 3).
Tests comment creation, listing on blogs, updating, deletion, and role permissions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.blog import Blog, BlogStatus
from app.models.comment import Comment
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_user_can_comment_on_approved_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user can create a comment on an approved blog post.
    """
    writer = User(
        email="c_writer1@example.com",
        username="c_writer1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    user = User(
        email="c_user1@example.com",
        username="c_user1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([writer, user])
    await db_session.commit()

    blog = Blog(
        title="Approved Tech Post",
        content="Interesting tech content.",
        status=BlogStatus.APPROVED,
        author_id=writer.id,
    )
    db_session.add(blog)
    await db_session.commit()

    user_token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {user_token}"}

    comment_payload = {"content": "Great article! Really enjoyed reading it."}
    response = await client.post(
        f"/api/v1/blogs/{blog.id}/comments",
        json=comment_payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == comment_payload["content"]
    assert data["author_id"] == str(user.id)
    assert data["blog_id"] == str(blog.id)


@pytest.mark.asyncio
async def test_user_cannot_comment_on_pending_blog(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user cannot comment on a pending blog post.
    """
    writer = User(
        email="c_writer2@example.com",
        username="c_writer2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    user = User(
        email="c_user2@example.com",
        username="c_user2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([writer, user])
    await db_session.commit()

    pending_blog = Blog(
        title="Pending Draft",
        content="Secret draft.",
        status=BlogStatus.PENDING,
        author_id=writer.id,
    )
    db_session.add(pending_blog)
    await db_session.commit()

    user_token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {user_token}"}

    response = await client.post(
        f"/api/v1/blogs/{pending_blog.id}/comments",
        json={"content": "Trying to comment on draft."},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_user_can_update_own_comment(client: AsyncClient, db_session: AsyncSession):
    """
    Test user can update their own comment text.
    """
    user = User(
        email="c_user3@example.com",
        username="c_user3",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    writer = User(
        email="c_writer3@example.com",
        username="c_writer3",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user, writer])
    await db_session.commit()

    blog = Blog(
        title="Approved Blog 3",
        content="Content 3.",
        status=BlogStatus.APPROVED,
        author_id=writer.id,
    )
    db_session.add(blog)
    await db_session.commit()

    comment = Comment(
        content="Original comment text.",
        blog_id=blog.id,
        author_id=user.id,
    )
    db_session.add(comment)
    await db_session.commit()

    user_token = create_access_token(subject=user.id)
    headers = {"Authorization": f"Bearer {user_token}"}

    response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "Updated comment text v2."},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated comment text v2."


@pytest.mark.asyncio
async def test_user_cannot_update_other_user_comment(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Test user 2 cannot update user 1's comment (403 Forbidden).
    """
    user1 = User(
        email="c_u1@example.com",
        username="c_u1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    user2 = User(
        email="c_u2@example.com",
        username="c_u2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    writer = User(
        email="c_w4@example.com",
        username="c_w4",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user1, user2, writer])
    await db_session.commit()

    blog = Blog(
        title="Blog 4",
        content="Content 4",
        status=BlogStatus.APPROVED,
        author_id=writer.id,
    )
    db_session.add(blog)
    await db_session.commit()

    comment = Comment(
        content="User 1 Comment",
        blog_id=blog.id,
        author_id=user1.id,
    )
    db_session.add(comment)
    await db_session.commit()

    user2_token = create_access_token(subject=user2.id)
    headers = {"Authorization": f"Bearer {user2_token}"}

    response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "Malicious edit attempt"},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_delete_any_comment(client: AsyncClient, db_session: AsyncSession):
    """
    Test Admin can delete any comment on a blog.
    """
    user = User(
        email="c_u5@example.com",
        username="c_u5",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    writer = User(
        email="c_w5@example.com",
        username="c_w5",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    admin = User(
        email="c_admin5@example.com",
        username="c_admin5",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user, writer, admin])
    await db_session.commit()

    blog = Blog(
        title="Blog 5",
        content="Content 5",
        status=BlogStatus.APPROVED,
        author_id=writer.id,
    )
    db_session.add(blog)
    await db_session.commit()

    comment = Comment(
        content="Comment to delete",
        blog_id=blog.id,
        author_id=user.id,
    )
    db_session.add(comment)
    await db_session.commit()

    admin_token = create_access_token(subject=admin.id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.delete(
        f"/api/v1/comments/{comment.id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Comment deleted successfully."
