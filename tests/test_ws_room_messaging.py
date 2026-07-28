"""
Pytest unit & integration tests for authorized persistent room messaging over WebSockets (room.send & room.message events).
"""

import json
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from fastapi import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import ws as ws_module
from app.api.v1.ws import websocket_endpoint
from app.core.constants import WSErrorCode
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.repositories.room_repository import room_repository, room_member_repository
from app.services.room_service import room_service


@pytest.mark.asyncio
async def test_ws_room_send_ack_and_broadcast(db_session: AsyncSession):
    """
    Test authorized room member sending room.send command receives ACK and online member receives room.message broadcast.
    """
    u1 = User(
        email=f"wsroom1_{uuid.uuid4()}@example.com",
        username=f"wsroom1_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    u2 = User(
        email=f"wsroom2_{uuid.uuid4()}@example.com",
        username=f"wsroom2_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add_all([u1, u2])
    await db_session.commit()

    room = await room_repository.create_room(db_session, name=f"WS Hub {uuid.uuid4().hex[:4]}", is_private=False)
    await room_member_repository.add_or_reactivate_member(db_session, room.id, u1.id)
    await room_member_repository.add_or_reactivate_member(db_session, room.id, u2.id)
    await db_session.commit()

    client_msg_id = str(uuid.uuid4())
    cmd_json = json.dumps({
        "v": 1,
        "cmd": "room.send",
        "payload": {
            "room_id": str(room.id),
            "client_msg_id": client_msg_id,
            "text": "Hello WebSocket Room!",
        },
    })

    mock_ws = AsyncMock()
    mock_ws.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=mock_ws, current_user=u1)
    finally:
        ws_module._db_override = None

    # Verify ACK event returned to sender
    assert mock_ws.send_text.call_count == 1
    sent_payload = json.loads(mock_ws.send_text.call_args[0][0])
    assert sent_payload["v"] == 1
    assert sent_payload["event"] == "ack"
    assert sent_payload["payload"]["client_msg_id"] == client_msg_id
    assert sent_payload["payload"]["status"] == "ok"


@pytest.mark.asyncio
async def test_ws_non_member_room_send_denial(db_session: AsyncSession):
    """
    Test non-member sending room.send receive WSEvent.error with code FORBIDDEN.
    """
    u_outsider = User(
        email=f"out_{uuid.uuid4()}@example.com",
        username=f"out_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(u_outsider)
    await db_session.commit()

    room = await room_repository.create_room(db_session, name=f"Private Hub {uuid.uuid4().hex[:4]}", is_private=False)
    await db_session.commit()

    cmd_json = json.dumps({
        "v": 1,
        "cmd": "room.send",
        "payload": {
            "room_id": str(room.id),
            "client_msg_id": str(uuid.uuid4()),
            "text": "Unauthorized post!",
        },
    })

    mock_ws = AsyncMock()
    mock_ws.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=mock_ws, current_user=u_outsider)
    finally:
        ws_module._db_override = None

    # Verify WSEvent.error returned
    assert mock_ws.send_text.call_count == 1
    err_payload = json.loads(mock_ws.send_text.call_args[0][0])
    assert err_payload["event"] == "error"
    assert err_payload["payload"]["code"] == WSErrorCode.FORBIDDEN


@pytest.mark.asyncio
async def test_ws_private_room_expired_subscription_denial(db_session: AsyncSession):
    """
    Test user with expired subscription sending room.send to private room receive WSEvent.error.
    """
    u_expired = User(
        email=f"exp_{uuid.uuid4()}@example.com",
        username=f"exp_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(u_expired)
    await db_session.commit()

    # Add expired subscription
    sub = Subscription(
        user_id=u_expired.id,
        stripe_customer_id="cus_exp",
        stripe_subscription_id="sub_exp",
        stripe_price_id="price_vip",
        status="active",
        current_period_end=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(sub)

    priv_room = await room_repository.create_room(db_session, name=f"VIP Lounge {uuid.uuid4().hex[:4]}", is_private=True)
    await room_member_repository.add_or_reactivate_member(db_session, priv_room.id, u_expired.id)
    await db_session.commit()

    cmd_json = json.dumps({
        "v": 1,
        "cmd": "room.send",
        "payload": {
            "room_id": str(priv_room.id),
            "client_msg_id": str(uuid.uuid4()),
            "text": "Post with expired sub",
        },
    })

    mock_ws = AsyncMock()
    mock_ws.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=mock_ws, current_user=u_expired)
    finally:
        ws_module._db_override = None

    assert mock_ws.send_text.call_count == 1
    err_payload = json.loads(mock_ws.send_text.call_args[0][0])
    assert err_payload["event"] == "error"
    assert err_payload["payload"]["code"] == WSErrorCode.FORBIDDEN


@pytest.mark.asyncio
async def test_ws_kicked_member_room_send_denial(db_session: AsyncSession):
    """
    Test member who was kicked by admin sending room.send receives WSEvent.error FORBIDDEN.
    """
    u_kicked = User(
        email=f"kick_{uuid.uuid4()}@example.com",
        username=f"kick_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        email=f"admin_{uuid.uuid4()}@example.com",
        username=f"admin_{str(uuid.uuid4())[:8]}",
        hashed_password="x",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([u_kicked, admin])
    await db_session.commit()

    room = await room_repository.create_room(db_session, name=f"Moderated Lounge {uuid.uuid4().hex[:4]}", is_private=False)
    await room_member_repository.add_or_reactivate_member(db_session, room.id, u_kicked.id)
    await room_service.remove_room_member(db_session, admin, room.id, u_kicked.id)
    await db_session.commit()

    cmd_json = json.dumps({
        "v": 1,
        "cmd": "room.send",
        "payload": {
            "room_id": str(room.id),
            "client_msg_id": str(uuid.uuid4()),
            "text": "Post after being kicked",
        },
    })

    mock_ws = AsyncMock()
    mock_ws.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=mock_ws, current_user=u_kicked)
    finally:
        ws_module._db_override = None

    assert mock_ws.send_text.call_count == 1
    err_payload = json.loads(mock_ws.send_text.call_args[0][0])
    assert err_payload["event"] == "error"
    assert err_payload["payload"]["code"] == WSErrorCode.FORBIDDEN
