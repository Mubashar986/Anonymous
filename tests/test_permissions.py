"""
Unit & Integration Pytest Suite for Capability Policy Evaluator and Permission Overrides.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


from app.models.user import User, UserRole
from app.models.permission import CapabilityEnum, OverrideEffectEnum
from app.services.policy_service import policy_evaluator
from app.core.security import get_password_hash, create_access_token


async def _create_test_users(db_session: AsyncSession):
    uid = str(uuid.uuid4())[:8]
    admin = User(
        email=f"admin_perm_{uid}@example.com",
        username=f"admin_perm_{uid}",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    writer = User(
        email=f"writer_perm_{uid}@example.com",
        username=f"writer_perm_{uid}",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=True,
    )
    normal = User(
        email=f"user_perm_{uid}@example.com",
        username=f"user_perm_{uid}",
        hashed_password=get_password_hash("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([admin, writer, normal])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(writer)
    await db_session.refresh(normal)
    return admin, writer, normal



@pytest.mark.asyncio
async def test_policy_evaluator_role_defaults(db_session: AsyncSession):
    """
    Test role-default baseline evaluation for USER, WRITER, and ADMIN.
    """
    admin, writer, normal = await _create_test_users(db_session)

    # USER role defaults
    assert await policy_evaluator.evaluate_capability(db_session, normal, CapabilityEnum.CAN_FOLLOW) is True
    assert await policy_evaluator.evaluate_capability(db_session, normal, CapabilityEnum.CAN_SUBMIT_BLOG) is False
    assert await policy_evaluator.evaluate_capability(db_session, normal, CapabilityEnum.CAN_CREATE_ROOM) is False

    # WRITER role defaults
    assert await policy_evaluator.evaluate_capability(db_session, writer, CapabilityEnum.CAN_SUBMIT_BLOG) is True
    assert await policy_evaluator.evaluate_capability(db_session, writer, CapabilityEnum.CAN_CREATE_ROOM) is True

    # ADMIN role defaults
    assert await policy_evaluator.evaluate_capability(db_session, admin, CapabilityEnum.CAN_SUBMIT_BLOG) is True
    assert await policy_evaluator.evaluate_capability(db_session, admin, CapabilityEnum.CAN_CREATE_ROOM) is True


@pytest.mark.asyncio
async def test_policy_evaluator_explicit_allow_override(db_session: AsyncSession):
    """
    Test that an explicit ALLOW override grants a capability to a USER whose role default is False.
    """
    admin, writer, normal = await _create_test_users(db_session)

    # Before override: USER cannot submit blogs
    assert await policy_evaluator.evaluate_capability(db_session, normal, CapabilityEnum.CAN_SUBMIT_BLOG) is False

    # Admin sets ALLOW override for CAN_SUBMIT_BLOG
    await policy_evaluator.set_user_override(
        db=db_session,
        actor=admin,
        target_user=normal,
        capability=CapabilityEnum.CAN_SUBMIT_BLOG,
        effect=OverrideEffectEnum.ALLOW,
        reason="Granted blog draft capability",
    )

    # After override: USER is now permitted to submit blogs
    assert await policy_evaluator.evaluate_capability(db_session, normal, CapabilityEnum.CAN_SUBMIT_BLOG) is True


@pytest.mark.asyncio
async def test_policy_evaluator_explicit_deny_override(db_session: AsyncSession):
    """
    Test that an explicit DENY override revokes a capability from a WRITER whose role default is True.
    """
    admin, writer, normal = await _create_test_users(db_session)

    # Before override: WRITER can submit blogs
    assert await policy_evaluator.evaluate_capability(db_session, writer, CapabilityEnum.CAN_SUBMIT_BLOG) is True

    # Admin sets DENY override for CAN_SUBMIT_BLOG
    await policy_evaluator.set_user_override(
        db=db_session,
        actor=admin,
        target_user=writer,
        capability=CapabilityEnum.CAN_SUBMIT_BLOG,
        effect=OverrideEffectEnum.DENY,
        reason="Moderation mute on blog submissions",
    )

    # After override: Explicit DENY wins over role default True
    assert await policy_evaluator.evaluate_capability(db_session, writer, CapabilityEnum.CAN_SUBMIT_BLOG) is False


@pytest.mark.asyncio
async def test_admin_cannot_modify_own_overrides(db_session: AsyncSession):
    """
    Test that an administrator cannot set permission overrides on their own account.
    """
    admin, writer, normal = await _create_test_users(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await policy_evaluator.set_user_override(
            db=db_session,
            actor=admin,
            target_user=admin,
            capability=CapabilityEnum.CAN_SUBMIT_BLOG,
            effect=OverrideEffectEnum.DENY,
        )
    assert exc_info.value.status_code == 400
    assert "cannot modify their own permission overrides" in exc_info.value.detail


@pytest.mark.asyncio
async def test_admin_permissions_api_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Test GET /users/{id}/permissions, PUT /users/{id}/permissions, and GET /users/{id}/permissions/audit via HTTP.
    """
    admin, writer, normal = await _create_test_users(db_session)

    admin_token = create_access_token(subject=admin.id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Fetch user capabilities
    resp = await client.get(f"/api/v1/users/{normal.id}/permissions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == str(normal.id)
    assert len(data["capabilities"]) == len(CapabilityEnum)

    # 2. Set ALLOW override on CAN_CREATE_ROOM
    put_resp = await client.put(
        f"/api/v1/users/{normal.id}/permissions",
        json={
            "capability": "can_create_room",
            "effect": "allow",
            "reason": "VIP room creation granted",
        },
        headers=headers,
    )
    assert put_resp.status_code == 200

    # 3. Verify audit log entry created
    audit_resp = await client.get(f"/api/v1/users/{normal.id}/permissions/audit", headers=headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert len(audit_data) >= 1
    assert audit_data[0]["capability"] == "can_create_room"
    assert audit_data[0]["new_state"] == "allow"


@pytest.mark.asyncio
async def test_non_admin_forbidden_from_permissions_api(client: AsyncClient, db_session: AsyncSession):
    """
    Test that normal users and writers receive HTTP 403 Forbidden when calling permission endpoints.
    """
    admin, writer, normal = await _create_test_users(db_session)

    user_token = create_access_token(subject=normal.id)
    headers = {"Authorization": f"Bearer {user_token}"}

    resp = await client.get(f"/api/v1/users/{writer.id}/permissions", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_capability_denial_blocks_feature_action(client: AsyncClient, db_session: AsyncSession):
    """
    Test that an explicit DENY override on CAN_FOLLOW blocks POST /follows with HTTP 403 Forbidden.
    """
    admin, writer, normal = await _create_test_users(db_session)

    # 1. Admin sets explicit DENY override on normal user for CAN_FOLLOW
    await policy_evaluator.set_user_override(
        db=db_session,
        actor=admin,
        target_user=normal,
        capability=CapabilityEnum.CAN_FOLLOW,
        effect=OverrideEffectEnum.DENY,
        reason="Sanctioned from following users",
    )

    # 2. Normal user attempts POST /follows
    user_token = create_access_token(subject=normal.id)
    headers = {"Authorization": f"Bearer {user_token}"}
    follow_resp = await client.post(
        "/api/v1/follows",
        json={"target_user_id": str(writer.id)},
        headers=headers,
    )
    assert follow_resp.status_code == 403
    assert "lacks required capability 'can_follow'" in follow_resp.json()["error"]["message"]


