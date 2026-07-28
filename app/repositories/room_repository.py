"""
Repository Layer for Community Room, Room Request, Room Member, and Room Message operations.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room, RoomRequest, RoomRequestStatus, RoomMember, RoomMessage

logger = logging.getLogger(__name__)


class RoomRequestRepository:
    """
    Data Access Object (DAO) for RoomRequest entities.
    """

    async def create_request(
        self, db: AsyncSession, requester_id: uuid.UUID, name: str, is_private: bool
    ) -> RoomRequest:
        """
        Create a new pending room creation request.
        """
        try:
            req = RoomRequest(requester_id=requester_id, name=name, is_private=is_private)
            db.add(req)
            await db.flush()
            return req
        except SQLAlchemyError as e:
            logger.error(f"Database error creating room request '{name}': {e}")
            raise

    async def get_by_id(self, db: AsyncSession, request_id: uuid.UUID) -> Optional[RoomRequest]:
        """
        Fetch room request by primary key with requester relationship loaded.
        """
        try:
            stmt = (
                select(RoomRequest)
                .where(RoomRequest.id == request_id)
                .options(selectinload(RoomRequest.requester))
            )
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching room request {request_id}: {e}")
            raise

    async def get_by_id_for_update(
        self, db: AsyncSession, request_id: uuid.UUID
    ) -> Optional[RoomRequest]:
        """
        Fetch room request with row-level database lock FOR UPDATE.
        """
        try:
            stmt = (
                select(RoomRequest)
                .where(RoomRequest.id == request_id)
                .with_for_update()
            )
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error locking room request {request_id}: {e}")
            raise

    async def list_pending_requests(
        self, db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> List[RoomRequest]:
        """
        List all pending room requests ordered by creation time.
        """
        try:
            stmt = (
                select(RoomRequest)
                .where(RoomRequest.status == RoomRequestStatus.PENDING)
                .order_by(RoomRequest.created_at.asc())
                .offset(skip)
                .limit(limit)
                .options(selectinload(RoomRequest.requester))
            )
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error listing pending room requests: {e}")
            raise

    async def list_user_requests(
        self, db: AsyncSession, requester_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[RoomRequest]:
        """
        List room requests submitted by a specific user.
        """
        try:
            stmt = (
                select(RoomRequest)
                .where(RoomRequest.requester_id == requester_id)
                .order_by(RoomRequest.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error listing user room requests for {requester_id}: {e}")
            raise

    async def update_status(
        self,
        db: AsyncSession,
        request_id: uuid.UUID,
        status: RoomRequestStatus,
        decision_by_id: uuid.UUID,
    ) -> Optional[RoomRequest]:
        """
        Update request status to APPROVED or REJECTED with decision metadata.
        """
        try:
            now = datetime.now(timezone.utc)
            req = await self.get_by_id(db, request_id)
            if not req:
                return None
            req.status = status
            req.decision_by_id = decision_by_id
            req.decision_at = now
            await db.flush()
            return req
        except SQLAlchemyError as e:
            logger.error(f"Database error updating request status for {request_id}: {e}")
            raise


class RoomRepository:
    """
    Data Access Object (DAO) for Room entities.
    """

    async def create_room(self, db: AsyncSession, name: str, is_private: bool) -> Room:
        """
        Create a new community room.
        """
        try:
            room = Room(name=name, is_private=is_private)
            db.add(room)
            await db.flush()
            return room
        except SQLAlchemyError as e:
            logger.error(f"Database error creating room '{name}': {e}")
            raise

    async def get_by_id(self, db: AsyncSession, room_id: uuid.UUID) -> Optional[Room]:
        """
        Fetch room by primary key.
        """
        try:
            stmt = select(Room).where(Room.id == room_id)
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching room {room_id}: {e}")
            raise

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Room]:
        """
        Fetch room by case-insensitive name.
        """
        try:
            stmt = select(Room).where(func.lower(Room.name) == func.lower(name))
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching room by name '{name}': {e}")
            raise

    async def list_rooms(
        self, db: AsyncSession, include_archived: bool = False, skip: int = 0, limit: int = 50
    ) -> List[Room]:
        """
        List community rooms with optional inclusion of archived rooms.
        """
        try:
            stmt = select(Room)
            if not include_archived:
                stmt = stmt.where(Room.is_archived == False)
            stmt = stmt.order_by(Room.created_at.desc()).offset(skip).limit(limit)
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error listing rooms: {e}")
            raise

    async def update_archived(
        self, db: AsyncSession, room_id: uuid.UUID, is_archived: bool
    ) -> Optional[Room]:
        """
        Archive or unarchive a community room.
        """
        try:
            room = await self.get_by_id(db, room_id)
            if not room:
                return None
            room.is_archived = is_archived
            await db.flush()
            return room
        except SQLAlchemyError as e:
            logger.error(f"Database error archiving room {room_id}: {e}")
            raise


class RoomMemberRepository:
    """
    Data Access Object (DAO) for RoomMember entities.
    """

    async def add_or_reactivate_member(
        self, db: AsyncSession, room_id: uuid.UUID, user_id: uuid.UUID
    ) -> RoomMember:
        """
        Add a new member to a room, or re-activate membership if previously removed.
        """
        try:
            stmt = select(RoomMember).where(
                RoomMember.room_id == room_id, RoomMember.user_id == user_id
            )
            res = await db.execute(stmt)
            member = res.scalar_one_or_none()
            if member:
                member.removed_at = None
                member.removed_by_id = None
                member.joined_at = datetime.now(timezone.utc)
            else:
                member = RoomMember(room_id=room_id, user_id=user_id)
                db.add(member)
            await db.flush()
            return member
        except SQLAlchemyError as e:
            logger.error(f"Database error adding/reactivating member ({user_id} in {room_id}): {e}")
            raise

    async def remove_member(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        removed_by_id: uuid.UUID,
    ) -> Optional[RoomMember]:
        """
        Soft-remove a member from a room by setting removed_at and removed_by_id.
        """
        try:
            stmt = select(RoomMember).where(
                RoomMember.room_id == room_id, RoomMember.user_id == user_id
            )
            res = await db.execute(stmt)
            member = res.scalar_one_or_none()
            if not member:
                return None
            member.removed_at = datetime.now(timezone.utc)
            member.removed_by_id = removed_by_id
            await db.flush()
            return member
        except SQLAlchemyError as e:
            logger.error(f"Database error removing member ({user_id} from {room_id}): {e}")
            raise

    async def get_membership(
        self, db: AsyncSession, room_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[RoomMember]:
        """
        Fetch room membership record regardless of active status.
        """
        try:
            stmt = select(RoomMember).where(
                RoomMember.room_id == room_id, RoomMember.user_id == user_id
            )
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching membership ({user_id} in {room_id}): {e}")
            raise

    async def is_active_member(
        self, db: AsyncSession, room_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """
        Check if user is currently an active member (not removed).
        """
        try:
            member = await self.get_membership(db, room_id, user_id)
            return member is not None and member.removed_at is None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking active membership ({user_id} in {room_id}): {e}")
            raise

    async def list_members(
        self, db: AsyncSession, room_id: uuid.UUID, active_only: bool = True
    ) -> List[RoomMember]:
        """
        List members of a room.
        """
        try:
            stmt = select(RoomMember).where(RoomMember.room_id == room_id)
            if active_only:
                stmt = stmt.where(RoomMember.removed_at == None)
            stmt = stmt.options(selectinload(RoomMember.user))
            res = await db.execute(stmt)
            return list(res.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error listing members for room {room_id}: {e}")
            raise


class RoomMessageRepository:
    """
    Data Access Object (DAO) for RoomMessage entities.
    """

    async def create(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        sender_id: uuid.UUID,
        client_msg_id: uuid.UUID,
        text: str,
    ) -> RoomMessage:
        """
        Persist a room message, returning existing record if client_msg_id is repeated.
        """
        try:
            existing = await self.get_by_client_msg_id(db, client_msg_id)
            if existing:
                return existing
            msg = RoomMessage(
                room_id=room_id,
                sender_id=sender_id,
                client_msg_id=client_msg_id,
                text=text,
            )
            db.add(msg)
            await db.flush()
            return msg
        except SQLAlchemyError as e:
            logger.error(f"Database error creating room message for room {room_id}: {e}")
            raise

    async def get_by_client_msg_id(
        self, db: AsyncSession, client_msg_id: uuid.UUID
    ) -> Optional[RoomMessage]:
        """
        Fetch room message by client_msg_id for idempotency.
        """
        try:
            stmt = (
                select(RoomMessage)
                .where(RoomMessage.client_msg_id == client_msg_id)
                .options(selectinload(RoomMessage.sender))
            )
            res = await db.execute(stmt)
            return res.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching room message by client ID {client_msg_id}: {e}")
            raise

    async def get_history(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        before_timestamp: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[RoomMessage]:
        """
        Fetch cursor-paginated message history for a room ordered chronologically.
        """
        try:
            stmt = select(RoomMessage).where(RoomMessage.room_id == room_id)
            if before_timestamp:
                stmt = stmt.where(RoomMessage.created_at < before_timestamp)
            stmt = (
                stmt.order_by(RoomMessage.created_at.desc())
                .limit(limit)
                .options(selectinload(RoomMessage.sender))
            )
            res = await db.execute(stmt)
            msgs = list(res.scalars().all())
            msgs.reverse()
            return msgs
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching history for room {room_id}: {e}")
            raise


room_request_repository = RoomRequestRepository()
room_repository = RoomRepository()
room_member_repository = RoomMemberRepository()
room_message_repository = RoomMessageRepository()
