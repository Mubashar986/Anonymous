"""
API Router for Community Rooms and Room Request REST endpoints.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.dependencies.auth import get_current_active_user, require_roles, require_capability
from app.models.permission import CapabilityEnum
from app.models.user import User, UserRole

from app.models.room import RoomMember, RoomMessage
from app.repositories.room_repository import (
    room_request_repository,
    room_repository,
    room_member_repository,
)
from app.schemas.room import (
    RoomRequestCreate,
    RoomRequestApprove,
    RoomRequestResponse,
    RoomCreateDirect,
    RoomResponse,
    RoomApproveResponse,
    RoomListResponse,
    RoomRequestListResponse,
    RoomMemberResponse,
    RoomMemberListResponse,
    RoomMessageResponse,
    RoomMessageListResponse,
)
from app.services.room_service import room_service

router = APIRouter(tags=["Community Rooms"])


# -------------------------------------------------------------------------
# User Room Request Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/rooms/requests",
    response_model=RoomRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a community room request",
)
async def submit_room_request(
    data: RoomRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_capability(CapabilityEnum.CAN_REQUEST_ROOM)),
):
    """
    Allow authenticated non-admin or writer users to propose a new community room.
    """
    return await room_service.submit_room_request(
        db, current_user, data.name, data.is_private
    )


@router.get(
    "/rooms/requests/me",
    response_model=RoomRequestListResponse,
    summary="View current user's submitted room requests",
)
async def list_my_room_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List room creation requests submitted by the current user.
    """
    requests = await room_request_repository.list_user_requests(
        db, current_user.id, skip, limit
    )
    return RoomRequestListResponse(items=requests, total=len(requests))


# -------------------------------------------------------------------------
# Public Room Listing Endpoint
# -------------------------------------------------------------------------

from sqlalchemy import select

@router.get(
    "/rooms",
    response_model=RoomListResponse,
    summary="List active community rooms",
)
async def list_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List active (non-archived) public and private community rooms.
    """
    rooms = await room_repository.list_rooms(
        db, include_archived=False, skip=skip, limit=limit
    )

    # Fetch active joined room IDs for current_user
    joined_stmt = select(RoomMember.room_id).where(
        RoomMember.user_id == current_user.id,
        RoomMember.removed_at.is_(None),
    )
    joined_res = await db.execute(joined_stmt)
    joined_ids = set(joined_res.scalars().all())

    items = []
    for r in rooms:
        resp = RoomResponse.model_validate(r)
        resp.is_joined = r.id in joined_ids
        items.append(resp)

    return RoomListResponse(items=items, total=len(items))


@router.post(
    "/rooms/{room_id}/join",
    response_model=RoomMemberResponse,
    summary="Join a community room",
)
async def join_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Join a public or private community room.
    Private rooms evaluate active Stripe subscription entitlement (or Admin bypass).
    """
    member = await room_service.join_room(db, current_user, room_id)
    resp = RoomMemberResponse.model_validate(member)
    resp.username = current_user.username
    return resp


@router.delete(
    "/rooms/{room_id}/leave",
    response_model=RoomMemberResponse,
    summary="Leave a community room",
)
async def leave_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Voluntarily leave a community room.
    """
    member = await room_service.leave_room(db, current_user, room_id)
    resp = RoomMemberResponse.model_validate(member)
    resp.username = current_user.username
    return resp


@router.get(
    "/rooms/{room_id}/members",
    response_model=RoomMemberListResponse,
    summary="List active members of a room",
)
async def list_room_members(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List active members of a room with usernames.
    Access requires subscription entitlement for private rooms.
    """
    room = await room_repository.get_by_id(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    await room_service.check_room_access_entitlement(db, current_user, room)

    stmt = (
        select(RoomMember, User.username)
        .join(User, User.id == RoomMember.user_id)
        .where(RoomMember.room_id == room_id, RoomMember.removed_at.is_(None))
        .order_by(RoomMember.joined_at.asc())
    )
    res = await db.execute(stmt)
    items = []
    for member, username in res.all():
        item = RoomMemberResponse.model_validate(member)
        item.username = username
        items.append(item)

    return RoomMemberListResponse(items=items, total=len(items))


@router.get(
    "/rooms/{room_id}/messages",
    response_model=RoomMessageListResponse,
    summary="Get room chat history",
)
async def get_room_messages(
    room_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fetch historical room chat messages with sender usernames.
    Requires active membership and private subscription entitlement.
    """
    room = await room_repository.get_by_id(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    await room_service.check_room_access_entitlement(db, current_user, room)

    stmt = (
        select(RoomMessage, User.username)
        .join(User, User.id == RoomMessage.sender_id)
        .where(RoomMessage.room_id == room_id)
    )
    if before:
        stmt = stmt.where(RoomMessage.created_at < before)
    stmt = stmt.order_by(RoomMessage.created_at.asc()).limit(limit)

    res = await db.execute(stmt)
    items = []
    for msg, username in res.all():
        item = RoomMessageResponse.model_validate(msg)
        item.sender_username = username
        items.append(item)

    return RoomMessageListResponse(items=items, total=len(items))


# -------------------------------------------------------------------------
# Administrator Endpoints
# -------------------------------------------------------------------------

@router.get(
    "/admin/rooms/requests",
    response_model=RoomRequestListResponse,
    summary="List pending room requests (Admin only)",
)
async def list_pending_room_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    List pending room creation requests for administrator review.
    """
    requests = await room_request_repository.list_pending_requests(db, skip, limit)
    return RoomRequestListResponse(items=requests, total=len(requests))


@router.post(
    "/admin/rooms/requests/{request_id}/approve",
    response_model=RoomApproveResponse,
    summary="Approve a room request and create room (Admin only)",
)
async def approve_room_request(
    request_id: uuid.UUID,
    data: Optional[RoomRequestApprove] = None,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Approve a pending request. Optionally override the room name.
    Creates the room and adds the requester as first member in one transaction.
    """
    final_name = data.final_name if data else None
    updated_req, room, member = await room_service.approve_room_request(
        db, admin_user, request_id, final_name=final_name
    )
    return RoomApproveResponse(request=updated_req, room=room)


@router.post(
    "/admin/rooms/requests/{request_id}/reject",
    response_model=RoomRequestResponse,
    summary="Reject a room request (Admin only)",
)
async def reject_room_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Reject a pending room request.
    """
    return await room_service.reject_room_request(db, admin_user, request_id)


@router.post(
    "/admin/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Directly create a room (Admin only)",
)
async def create_room_direct(
    data: RoomCreateDirect,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Create a community room directly without a request.
    """
    clean_name = data.name.strip()
    existing = await room_repository.get_by_name(db, clean_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room with this name already exists",
        )
    room = await room_repository.create_room(db, clean_name, data.is_private)
    await db.commit()
    return room


@router.patch(
    "/admin/rooms/{room_id}/archive",
    response_model=RoomResponse,
    summary="Archive a community room (Admin only)",
)
async def archive_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Archive a room to prevent new membership or messages.
    """
    return await room_service.archive_room(db, admin_user, room_id)


@router.delete(
    "/admin/rooms/{room_id}/members/{user_id}",
    response_model=RoomMemberResponse,
    summary="Remove a room member (Admin only)",
)
async def remove_room_member(
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Remove a member from a community room. Admin-only operation.
    Records removed_at timestamp and removed_by_id audit metadata.
    """
    return await room_service.remove_room_member(db, admin_user, room_id, user_id)
