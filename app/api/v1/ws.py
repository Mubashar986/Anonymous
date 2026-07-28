"""
WebSocket Endpoint & Command Dispatch Handler.
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection_manager import connection_manager
from app.database.database import get_db
from app.dependencies.ws_auth import get_current_user_ws
from app.models.user import User
from app.schemas.ws import (
    WSCommand,
    WSEvent,
    WSCommandName,
    WSEventName,
    WSErrorCode,
    DmSendPayload,
    DmMessagePayload,
    RoomSendPayload,
    RoomMessagePayload,
)
from app.services.conversation_service import conversation_service
from app.repositories.conversation_repository import conversation_repository
from app.services.room_service import room_service
from app.repositories.room_repository import room_member_repository
from app.services.policy_service import policy_evaluator
from app.models.permission import CapabilityEnum

logger = logging.getLogger(__name__)


router = APIRouter(tags=["websockets"])

# Test injection point — set this from tests to provide a mock db session
_db_override: Optional[AsyncSession] = None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
):
    """
    Main WebSocket Gateway Endpoint.
    Handles live command loop, ACK dispatch, and recipient push.
    """
    await connection_manager.connect(websocket, current_user.id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                command = WSCommand.model_validate_json(raw_data)
            except (ValidationError, Exception) as e:
                err_event = WSEvent.error(
                    code=WSErrorCode.INVALID_PAYLOAD,
                    detail=f"Malformed JSON or invalid command schema: {e}",
                )
                await websocket.send_text(err_event.model_dump_json())
                continue

            if command.cmd == WSCommandName.DM_SEND:
                try:
                    payload = DmSendPayload.model_validate(command.payload)
                except ValidationError as ve:
                    err_event = WSEvent.error(
                        code=WSErrorCode.INVALID_PAYLOAD,
                        detail=f"Invalid dm.send payload: {ve}",
                    )
                    await websocket.send_text(err_event.model_dump_json())
                    continue

                async def _process_dm_send(session: AsyncSession):
                    allowed = await policy_evaluator.evaluate_capability(
                        session, current_user, CapabilityEnum.CAN_SEND_DIRECT_MESSAGE
                    )
                    if not allowed:
                        raise HTTPException(
                            status_code=403,
                            detail="Action denied: user lacks required capability 'can_send_direct_message'.",
                        )

                    msg = await conversation_service.send_message(

                        session,
                        current_user=current_user,
                        conversation_id=payload.conversation_id,
                        client_msg_id=payload.client_msg_id,
                        text=payload.text,
                    )
                    # 1. Send ACK event back to sender socket
                    ack_event = WSEvent.ack(client_msg_id=msg.client_msg_id, msg_id=msg.id)
                    await websocket.send_text(ack_event.model_dump_json())

                    # 2. Live dispatch dm.message event to all conversation participants
                    conv = await conversation_repository.get_by_id(session, payload.conversation_id)
                    if conv:
                        dm_payload = DmMessagePayload(
                            msg_id=msg.id,
                            conversation_id=msg.conversation_id,
                            sender_id=msg.sender_id,
                            client_msg_id=msg.client_msg_id,
                            text=msg.text,
                            timestamp=msg.created_at.isoformat(),
                        )
                        new_msg_event = WSEvent(
                            v=1,
                            event=WSEventName.DM_MESSAGE,
                            payload=dm_payload.model_dump(mode="json"),
                        )
                        for p in conv.participants:
                            if p.user_id != current_user.id and connection_manager.is_user_online(p.user_id):
                                await connection_manager.send_personal_message(
                                    new_msg_event.model_dump(mode="json"), p.user_id
                                )

                if _db_override is not None:
                    try:
                        await _process_dm_send(_db_override)
                    except HTTPException as exc:
                        err_event = WSEvent.error(
                            code=WSErrorCode.FORBIDDEN,
                            detail=exc.detail if isinstance(exc.detail, str) else "Forbidden",
                        )
                        await websocket.send_text(err_event.model_dump_json())
                else:
                    async for session in get_db():
                        try:
                            await _process_dm_send(session)
                        except HTTPException as exc:
                            err_event = WSEvent.error(
                                code=WSErrorCode.FORBIDDEN,
                                detail=exc.detail if isinstance(exc.detail, str) else "Forbidden",
                            )
                            await websocket.send_text(err_event.model_dump_json())
                        break

            elif command.cmd == WSCommandName.ROOM_SEND:
                try:
                    payload = RoomSendPayload.model_validate(command.payload)
                except ValidationError as ve:
                    err_event = WSEvent.error(
                        code=WSErrorCode.INVALID_PAYLOAD,
                        detail=f"Invalid room.send payload: {ve}",
                    )
                    await websocket.send_text(err_event.model_dump_json())
                    continue

                async def _process_room_send(session: AsyncSession):
                    msg = await room_service.post_room_message(
                        session,
                        current_user=current_user,
                        room_id=payload.room_id,
                        client_msg_id=payload.client_msg_id,
                        text=payload.text,
                    )
                    # 1. Send ACK event back to sender socket
                    ack_event = WSEvent.ack(client_msg_id=msg.client_msg_id, msg_id=msg.id)
                    await websocket.send_text(ack_event.model_dump_json())

                    # 2. Live dispatch room.message event to all active room members
                    members = await room_member_repository.list_members(
                        session, payload.room_id, active_only=True
                    )
                    room_payload = RoomMessagePayload(
                        msg_id=msg.id,
                        room_id=msg.room_id,
                        sender_id=msg.sender_id,
                        text=msg.text,
                        timestamp=msg.created_at.isoformat(),
                        sender_username=current_user.username,
                    )
                    new_msg_event = WSEvent(
                        v=1,
                        event=WSEventName.ROOM_MESSAGE,
                        payload=room_payload.model_dump(mode="json"),
                    )
                    for m in members:
                        if m.user_id != current_user.id and connection_manager.is_user_online(m.user_id):
                            await connection_manager.send_personal_message(
                                new_msg_event.model_dump(mode="json"), m.user_id
                            )

                if _db_override is not None:
                    try:
                        await _process_room_send(_db_override)
                    except HTTPException as exc:
                        err_event = WSEvent.error(
                            code=WSErrorCode.FORBIDDEN,
                            detail=exc.detail if isinstance(exc.detail, str) else "Forbidden",
                        )
                        await websocket.send_text(err_event.model_dump_json())
                else:
                    async for session in get_db():
                        try:
                            await _process_room_send(session)
                        except HTTPException as exc:
                            err_event = WSEvent.error(
                                code=WSErrorCode.FORBIDDEN,
                                detail=exc.detail if isinstance(exc.detail, str) else "Forbidden",
                            )
                            await websocket.send_text(err_event.model_dump_json())
                        break

            else:
                err_event = WSEvent.error(
                    code=WSErrorCode.UNKNOWN_COMMAND,
                    detail=f"Unknown command '{command.cmd}'",
                )
                await websocket.send_text(err_event.model_dump_json())

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, current_user.id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket loop for user {current_user.id}: {e}")
        connection_manager.disconnect(websocket, current_user.id)
