"""
Unit tests for Role-Based Access Control (RBAC), User Roles, and Admin Promotion.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token


@pytest.mark.asyncio
async def test_user_signup_default_role(client: AsyncClient):
    """
    Test user signup sets default role to 'user', even if client sends role in payload.
    """
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "defaultroleuser@example.com",
            "username": "defaultroleuser",
            "password": "Password123!",
            "role": "admin",  # Malicious self-promotion attempt
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "defaultroleuser@example.com"
    assert data["role"] == "user"  # Must remain 'user'


@pytest.mark.asyncio
async def test_admin_can_promote_user(client: AsyncClient, db_session: AsyncSession):
    """
    Test Admin can promote a standard user to writer via PATCH /api/v1/users/{id}/role.
    """
    admin = User(
        email="admin_promoter@example.com",
        username="admin_promoter",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    target_user = User(
        email="user_to_promote@example.com",
        username="user_to_promote",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([admin, target_user])
    await db_session.commit()

    admin_token = create_access_token(subject=admin.id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.patch(
        f"/api/v1/users/{target_user.id}/role",
        json={"role": "writer"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "writer"


@pytest.mark.asyncio
async def test_non_admin_cannot_promote_user(client: AsyncClient, db_session: AsyncSession):
    """
    Test standard user cannot promote users (403 Forbidden).
    """
    user1 = User(
        email="normal_user1@example.com",
        username="normal_user1",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    user2 = User(
        email="normal_user2@example.com",
        username="normal_user2",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user1, user2])
    await db_session.commit()

    user1_token = create_access_token(subject=user1.id)
    headers = {"Authorization": f"Bearer {user1_token}"}

    response = await client.patch(
        f"/api/v1/users/{user2.id}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert response.status_code == 403
