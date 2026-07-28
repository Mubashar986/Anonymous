"""
Service Layer for Community Rooms business workflows, permissions, state transitions, and entitlement checks.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import WS_MAX_TEXT_LEN
from app.models.room import Room, RoomRequest, RoomRequestStatus, RoomMember, RoomMessage
from app.models.user import User, UserRole
from app.repositories.room_repository import (
    room_request_repository,
    room_repository,
    room_member_repository,
    room_message_repository,
)
from app.repositories.subscription_repository import subscription_repository
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationTypeEnum, NavigationTargetEnum

logger = logging.getLogger(__name__)


class RoomService:
    """
    Domain workflow service managing community rooms, requests, membership, paywalls, and room chat.
    """

    async def check_room_access_entitlement(
        self, db: AsyncSession, user: User, room: Room
    ) -> bool:
        """
        Verify if user has entitlement to access a private room.
        Public rooms allow any active account.
        Private rooms require an active Stripe subscription, or UserRole.ADMIN bypass.
        """
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive account",
            )
        if not room.is_private:
            return True
        if user.role == UserRole.ADMIN:
            return True

        sub = await subscription_repository.get_by_user_id(db, user.id)
        if not sub or sub.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="An active premium subscription is required to access this private room",
            )
        if sub.current_period_end:
            now = datetime.now(timezone.utc)
            period_end = sub.current_period_end
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)
            if period_end < now:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Subscription period has expired. Please renew your VIP subscription.",
                )
        return True

    async def submit_room_request(
        self, db: AsyncSession, current_user: User, name: str, is_private: bool
    ) -> RoomRequest:
        """
        Submit a new community room creation request.
        """
        clean_name = name.strip() if name else ""
        if not clean_name or len(clean_name) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room name must be between 1 and 50 characters",
            )

        existing_room = await room_repository.get_by_name(db, clean_name)
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A room with this name already exists",
            )

        req = await room_request_repository.create_request(
            db, current_user.id, clean_name, is_private
        )
        await db.commit()
        return req

    async def approve_room_request(
        self,
        db: AsyncSession,
        admin_user: User,
        request_id: uuid.UUID,
        final_name: Optional[str] = None,
    ) -> Tuple[RoomRequest, Room, RoomMember]:
        """
        Approve a room creation request atomically in one database transaction.
        Updates request status to APPROVED, creates the Room, and joins the requester as the first member.
        """
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can approve room requests",
            )

        req = await room_request_repository.get_by_id_for_update(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room request not found",
            )
        if req.status != RoomRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room request is already {req.status.value}",
            )

        target_name = (final_name.strip() if final_name else req.name).strip()
        existing_room = await room_repository.get_by_name(db, target_name)
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A room named '{target_name}' already exists",
            )

        # Single atomic database transaction execution
        updated_req = await room_request_repository.update_status(
            db, request_id, RoomRequestStatus.APPROVED, admin_user.id
        )
        room = await room_repository.create_room(db, target_name, req.is_private)
        member = await room_member_repository.add_or_reactivate_member(
            db, room.id, req.requester_id
        )

        # Emit room request approved notification
        await notification_service.create_notification_event(
            db=db,
            recipient_id=req.requester_id,
            actor_id=admin_user.id,
            actor_username=admin_user.username,
            event_type=NotificationTypeEnum.ROOM_REQUEST_APPROVED,
            target_type="room",
            target_id=room.id,
            title="Room Request Approved",
            summary_text=f"Your room request for '{room.name}' was approved.",
            navigation_target=NavigationTargetEnum.ROOM_DETAIL,
            navigation_params={"room_id": str(room.id)},
        )

        await db.commit()
        return updated_req, room, member

    async def reject_room_request(
        self, db: AsyncSession, admin_user: User, request_id: uuid.UUID
    ) -> RoomRequest:
        """
        Reject a pending room creation request.
        """
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reject room requests",
            )

        req = await room_request_repository.get_by_id_for_update(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room request not found",
            )
        if req.status != RoomRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room request is already {req.status.value}",
            )

        updated_req = await room_request_repository.update_status(
            db, request_id, RoomRequestStatus.REJECTED, admin_user.id
        )

        # Emit room request rejected notification
        await notification_service.create_notification_event(
            db=db,
            recipient_id=req.requester_id,
            actor_id=admin_user.id,
            actor_username=admin_user.username,
            event_type=NotificationTypeEnum.ROOM_REQUEST_REJECTED,
            target_type="room_request",
            target_id=req.id,
            title="Room Request Rejected",
            summary_text=f"Your room request for '{req.name}' was rejected.",
            navigation_target=NavigationTargetEnum.ROOM_LIST,
        )

        await db.commit()
        return updated_req

    async def join_room(
        self, db: AsyncSession, current_user: User, room_id: uuid.UUID
    ) -> RoomMember:
        """
        Join a public or private room. Enforces room status and subscription entitlement.
        """
        room = await room_repository.get_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )
        if room.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join an archived room",
            )

        await self.check_room_access_entitlement(db, current_user, room)

        member = await room_member_repository.add_or_reactivate_member(
            db, room.id, current_user.id
        )
        await db.commit()
        return member

    async def remove_room_member(
        self,
        db: AsyncSession,
        admin_user: User,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> RoomMember:
        """
        Remove a member from a room. Admin-only action.
        """
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can remove room members",
            )

        room = await room_repository.get_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        member = await room_member_repository.remove_member(
            db, room_id, target_user_id, admin_user.id
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this room",
            )

        await db.commit()
        return member

    async def archive_room(
        self, db: AsyncSession, admin_user: User, room_id: uuid.UUID
    ) -> Room:
        """
        Archive a room. Admin-only action.
        """
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can archive rooms",
            )

        room = await room_repository.update_archived(db, room_id, is_archived=True)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        await db.commit()
        return room

    async def post_room_message(
        self,
        db: AsyncSession,
        current_user: User,
        room_id: uuid.UUID,
        client_msg_id: uuid.UUID,
        text: str,
    ) -> RoomMessage:
        """
        Post a text message inside a community room.
        Validates room state, active membership, subscription entitlement, and text length limits.
        """
        room = await room_repository.get_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )
        if room.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot post messages to an archived room",
            )

        is_active = await room_member_repository.is_active_member(
            db, room_id, current_user.id
        )
        if not is_active and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be an active member to post in this room",
            )

        await self.check_room_access_entitlement(db, current_user, room)

        clean_text = text.strip() if text else ""
        if not clean_text or len(clean_text) > WS_MAX_TEXT_LEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message text must be between 1 and {WS_MAX_TEXT_LEN} characters",
            )

        msg = await room_message_repository.create(
            db,
            room_id=room_id,
            sender_id=current_user.id,
            client_msg_id=client_msg_id,
            text=clean_text,
        )
        await db.commit()
        return msg

    async def get_room_history(
        self,
        db: AsyncSession,
        current_user: User,
        room_id: uuid.UUID,
        before_timestamp: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[RoomMessage]:
        """
        Retrieve paginated chat history for a room.
        Requires active membership (or admin) and active subscription entitlement for private rooms.
        """
        room = await room_repository.get_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        is_active = await room_member_repository.is_active_member(
            db, room_id, current_user.id
        )
        if not is_active and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to room history",
            )

        await self.check_room_access_entitlement(db, current_user, room)

        return await room_message_repository.get_history(
            db, room_id, before_timestamp, limit
        )

    async def leave_room(
        self, db: AsyncSession, current_user: User, room_id: uuid.UUID
    ) -> RoomMember:
        """
        Allow a user to self-remove from a room.
        """
        room = await room_repository.get_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found",
            )

        member = await room_member_repository.remove_member(
            db, room_id, current_user.id, current_user.id
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not an active member of this room",
            )

        await db.commit()
        return member


room_service = RoomService()
