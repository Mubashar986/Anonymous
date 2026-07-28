"""
Integration tests for Authentication & User endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_signup_user_success(client: AsyncClient):
    """
    Test successful user registration.
    """
    payload = {
        "email": "tester@example.com",
        "username": "test_user",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    """
    Test registering with an email that is already registered.
    """
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "Password123!",
    }
    res1 = await client.post("/api/v1/auth/signup", json=payload)
    assert res1.status_code == 201

    # Attempt signup again with same email
    res2 = await client.post("/api/v1/auth/signup", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    Test authenticating with valid credentials.
    """
    # 1. Signup
    signup_payload = {
        "email": "login_user@example.com",
        "username": "login_user",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/signup", json=signup_payload)

    # 2. Login
    login_payload = {
        "email": signup_payload["email"],
        "password": signup_payload["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """
    Test authenticating with wrong password.
    """
    signup_payload = {
        "email": "wrong_pass@example.com",
        "username": "wrong_pass_user",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/signup", json=signup_payload)

    login_payload = {
        "email": signup_payload["email"],
        "password": "IncorrectPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    """
    Test accessing protected profile endpoint /users/me with Bearer token.
    """
    signup_payload = {
        "email": "profile@example.com",
        "username": "profile_user",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/signup", json=signup_payload)

    # Login to get access token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    access_token = login_res.json()["access_token"]

    # Access protected route with Authorization header
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == signup_payload["email"]


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """
    Test accessing protected route without Authorization header.
    """
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resend_verification_unverified_user(client: AsyncClient, db_session: AsyncSession):
    """Verify resend verification email succeeds for unverified user."""
    user = User(
        email="unverified_resend@example.com",
        username="unverified_resend",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/resend-verification?email=unverified_resend@example.com")
    assert response.status_code == 200
    assert "verification link has been sent" in response.json()["message"]


@pytest.mark.asyncio
async def test_resend_verification_already_verified(client: AsyncClient, db_session: AsyncSession):
    """Verify resend verification email raises 400 for already verified user."""
    user = User(
        email="already_verified@example.com",
        username="already_verified",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post("/api/v1/auth/resend-verification?email=already_verified@example.com")
    assert response.status_code == 400
    res_data = response.json()
    err_msg = res_data.get("error", {}).get("message") or res_data.get("detail", "")
    assert "already verified" in err_msg


@pytest.mark.asyncio
async def test_resend_verification_nonexistent_user(client: AsyncClient):
    """Verify resend verification email returns 200 silently for nonexistent email."""
    response = await client.post("/api/v1/auth/resend-verification?email=nonexistent@example.com")
    assert response.status_code == 200

