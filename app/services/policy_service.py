"""
Policy Evaluator Service for Authorization Precedence & Permission Overrides.

Precedence Order:
1. Active status check (Handled upstream by get_current_active_user)
2. Admin Guard: Admins hold full system authority and cannot have overrides or self-edits.
3. Explicit Deny override: Database override with is_allowed=False.
4. Explicit Allow override: Database override with is_allowed=True.
5. Role baseline default: Lookup in ROLE_DEFAULT_CAPABILITIES.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.permission import (
    CapabilityEnum,
    OverrideEffectEnum,
    UserPermissionOverride,
    PermissionAuditLog,
    ROLE_DEFAULT_CAPABILITIES,
)
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum


class PolicyEvaluatorService:
    """
    Centralized Policy Evaluation Service.
    """

    async def evaluate_capability(
        self,
        db: AsyncSession,
        user: User,
        capability: CapabilityEnum,
    ) -> bool:
        """
        Evaluate if a user is permitted to perform the specified capability.
        """
        # Step 2: Admins automatically hold all system capabilities
        if user.role == UserRole.ADMIN:
            return True

        # Query per-user database override
        stmt = select(UserPermissionOverride).where(
            UserPermissionOverride.user_id == user.id,
            UserPermissionOverride.capability == capability.value,
        )
        result = await db.execute(stmt)
        override = result.scalar_one_or_none()

        # Step 3 & 4: Explicit Deny / Allow override wins over role default
        if override is not None:
            return override.is_allowed

        # Step 5: Fallback to role baseline default
        role_defaults = ROLE_DEFAULT_CAPABILITIES.get(user.role.value, {})
        return role_defaults.get(capability, False)

    async def get_user_capabilities(
        self,
        db: AsyncSession,
        target_user: User,
    ) -> List[dict]:
        """
        Retrieve all capability statuses for a target user (defaults, overrides, effective).
        """
        stmt = select(UserPermissionOverride).where(
            UserPermissionOverride.user_id == target_user.id
        )
        result = await db.execute(stmt)
        overrides = {o.capability: o.is_allowed for o in result.scalars().all()}

        role_defaults = ROLE_DEFAULT_CAPABILITIES.get(target_user.role.value, {})
        capabilities_summary = []

        for cap in CapabilityEnum:
            r_default = role_defaults.get(cap, False)
            ov_val = overrides.get(cap.value)

            if ov_val is True:
                ov_effect = OverrideEffectEnum.ALLOW
                effective = True
            elif ov_val is False:
                ov_effect = OverrideEffectEnum.DENY
                effective = False
            else:
                ov_effect = None
                effective = r_default

            capabilities_summary.append({
                "capability": cap,
                "role_default": r_default,
                "override": ov_effect,
                "effective_permission": effective,
            })

        return capabilities_summary

    async def set_user_override(
        self,
        db: AsyncSession,
        actor: User,
        target_user: User,
        capability: CapabilityEnum,
        effect: OverrideEffectEnum,
        reason: Optional[str] = None,
    ) -> None:
        """
        Create, update, or clear (INHERIT) a capability override for a target user and record an audit entry.
        Enforces admin self-edit and target-admin security boundaries.
        """
        if actor.id == target_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot modify their own permission overrides.",
            )

        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission overrides cannot be set on administrator accounts.",
            )

        stmt = select(UserPermissionOverride).where(
            UserPermissionOverride.user_id == target_user.id,
            UserPermissionOverride.capability == capability.value,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        prev_state = None
        if existing is not None:
            prev_state = "allow" if existing.is_allowed else "deny"
        else:
            prev_state = "inherit"

        if effect == OverrideEffectEnum.INHERIT:
            if existing is not None:
                await db.delete(existing)
                new_state = "inherit"
            else:
                return
        else:
            is_allowed = (effect == OverrideEffectEnum.ALLOW)
            new_state = effect.value
            if existing is not None:
                existing.is_allowed = is_allowed
            else:
                new_override = UserPermissionOverride(
                    user_id=target_user.id,
                    capability=capability.value,
                    is_allowed=is_allowed,
                )
                db.add(new_override)

        # Record immutable audit log entry
        audit_entry = PermissionAuditLog(
            actor_id=actor.id,
            target_id=target_user.id,
            capability=capability.value,
            previous_state=prev_state,
            new_state=new_state,
            reason=reason,
        )
        db.add(audit_entry)

        # Emit PERMISSION_OVERRIDE_CHANGED notification to target user
        await notification_service.create_notification_event(
            db=db,
            recipient_id=target_user.id,
            actor_id=actor.id,
            actor_username=actor.username,
            event_type=NotificationTypeEnum.PERMISSION_OVERRIDE_CHANGED,
            target_type="user",
            target_id=target_user.id,
            title="Permission Updated",
            summary_text=f"Your permission for '{capability.value}' was updated to '{new_state}'.",
            navigation_target=NavigationTargetEnum.PROFILE,
            navigation_params={"user_id": str(target_user.id)},
        )

        await db.commit()


policy_evaluator = PolicyEvaluatorService()
