import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.blog import Blog, BlogStatus
from app.models.follow import Follow


@pytest_asyncio.fixture
async def profile_users(db_session: AsyncSession):
    """Fixture providing created users and valid JWT headers for profile testing."""
    u1 = User(
        email=f"prof_u1_{uuid.uuid4()}@example.com",
        username=f"prof_u1_{str(uuid.uuid4())[:8]}",
        hashed_password="hashed_password_placeholder",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"prof_u2_{uuid.uuid4()}@example.com",
        username=f"prof_u2_{str(uuid.uuid4())[:8]}",
        hashed_password="hashed_password_placeholder",
        role=UserRole.USER,
        is_active=True,
        bio="Hello world, I am user 2",
    )
    w1 = User(
        email=f"prof_w1_{uuid.uuid4()}@example.com",
        username=f"prof_w1_{str(uuid.uuid4())[:8]}",
        hashed_password="hashed_password_placeholder",
        role=UserRole.WRITER,
        is_active=True,
        bio="I am a professional tech writer.",
    )
    admin1 = User(
        email=f"prof_admin1_{uuid.uuid4()}@example.com",
        username=f"prof_admin1_{str(uuid.uuid4())[:8]}",
        hashed_password="hashed_password_placeholder",
        role=UserRole.ADMIN,
        is_active=True,
    )
    inactive_u = User(
        email=f"prof_inact_{uuid.uuid4()}@example.com",
        username=f"prof_inact_{str(uuid.uuid4())[:8]}",
        hashed_password="hashed_password_placeholder",
        role=UserRole.USER,
        is_active=False,
    )

    db_session.add_all([u1, u2, w1, admin1, inactive_u])
    await db_session.commit()

    # Generate some blogs for writer w1
    blog_approved = Blog(
        title="Approved Article",
        content="This is the approved article content.",
        status=BlogStatus.APPROVED,
        is_premium=False,
        author_id=w1.id,
    )
    blog_pending = Blog(
        title="Pending Article",
        content="This is a draft/pending article content.",
        status=BlogStatus.PENDING,
        is_premium=False,
        author_id=w1.id,
    )
    db_session.add_all([blog_approved, blog_pending])
    await db_session.commit()

    # Generate follow relation: u1 follows w1
    follow = Follow(follower_id=u1.id, target_id=w1.id)
    db_session.add(follow)
    await db_session.commit()

    t1 = create_access_token(subject=str(u1.id))
    t2 = create_access_token(subject=str(u2.id))
    t_writer = create_access_token(subject=str(w1.id))
    
    return {
        "u1": u1,
        "u2": u2,
        "w1": w1,
        "admin1": admin1,
        "inactive_u": inactive_u,
        "headers_u1": {"Authorization": f"Bearer {t1}"},
        "headers_u2": {"Authorization": f"Bearer {t2}"},
        "headers_writer": {"Authorization": f"Bearer {t_writer}"},
    }


@pytest.mark.asyncio
async def test_get_profile_success(client: AsyncClient, profile_users: dict):
    # u2 fetches w1's profile
    target_id = profile_users["w1"].id
    headers = profile_users["headers_u2"]

    response = await client.get(
        f"/api/v1/users/{target_id}/profile",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == profile_users["w1"].username
    assert data["role"] == UserRole.WRITER.value
    assert data["bio"] == "I am a professional tech writer."
    assert data["followers_count"] == 1
    assert data["following_count"] == 0
    assert data["is_following"] is False  # u2 is not following w1
    assert "email" not in data
    assert "is_active" not in data
    
    # Assert writer articles contain only the approved blog
    assert data["articles"] is not None
    assert len(data["articles"]) == 1
    assert data["articles"][0]["title"] == "Approved Article"
    assert data["articles"][0]["status"] == "approved"


@pytest.mark.asyncio
async def test_get_profile_with_follow_state(client: AsyncClient, profile_users: dict):
    # u1 follows w1 in fixture; u1 fetches w1's profile
    target_id = profile_users["w1"].id
    headers = profile_users["headers_u1"]

    response = await client.get(
        f"/api/v1/users/{target_id}/profile",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_following"] is True


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient, profile_users: dict):
    target_id = profile_users["u2"].id
    response = await client.get(
        f"/api/v1/users/{target_id}/profile",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_profile_inactive_404(client: AsyncClient, profile_users: dict):
    target_id = profile_users["inactive_u"].id
    headers = profile_users["headers_u1"]

    response = await client.get(
        f"/api/v1/users/{target_id}/profile",
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_profile_admin_404(client: AsyncClient, profile_users: dict):
    target_id = profile_users["admin1"].id
    headers = profile_users["headers_u1"]

    response = await client.get(
        f"/api/v1/users/{target_id}/profile",
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_profile_missing_404(client: AsyncClient, profile_users: dict):
    missing_id = uuid.uuid4()
    headers = profile_users["headers_u1"]

    response = await client.get(
        f"/api/v1/users/{missing_id}/profile",
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_bio_via_patch_me(client: AsyncClient, profile_users: dict):
    # 1. Update bio
    headers = profile_users["headers_u1"]
    patch_response = await client.patch(
        "/api/v1/users/me",
        json={"bio": "Updated biography!"},
        headers=headers,
    )
    assert patch_response.status_code == status.HTTP_200_OK

    # 2. Get profile of self to confirm bio is updated
    my_id = profile_users["u1"].id
    profile_response = await client.get(
        f"/api/v1/users/{my_id}/profile",
        headers=headers,
    )
    assert profile_response.status_code == status.HTTP_200_OK
    data = profile_response.json()
    assert data["bio"] == "Updated biography!"


@pytest.mark.asyncio
async def test_writer_articles_pagination(client: AsyncClient, db_session: AsyncSession, profile_users: dict):
    writer_id = profile_users["w1"].id
    headers = profile_users["headers_u2"]

    # Create 3 extra approved blogs (total 4 approved including fixture blog)
    for i in range(3):
        extra_blog = Blog(
            title=f"Extra Approved Article {i}",
            content=f"Content {i}",
            status=BlogStatus.APPROVED,
            is_premium=False,
            author_id=writer_id,
        )
        db_session.add(extra_blog)
    await db_session.commit()

    # Query profile with limit=2 (page 1)
    res = await client.get(f"/api/v1/users/{writer_id}/profile?skip=0&limit=2", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["articles"]) == 2

    # Query profile with limit=2 skip=2 (page 2)
    res2 = await client.get(f"/api/v1/users/{writer_id}/profile?skip=2&limit=2", headers=headers)
    assert res2.status_code == status.HTTP_200_OK
    data2 = res2.json()
    assert len(data2["articles"]) == 2
    # Assert different blogs returned
    assert data["articles"][0]["id"] != data2["articles"][0]["id"]
