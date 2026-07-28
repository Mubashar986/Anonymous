"""
End-to-End WebSocket Live Messaging Integration Test Suite.
"""

import json
import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocketDisconnect

from app.api.v1 import ws as ws_module
from app.api.v1.ws import websocket_endpoint
from app.core.connection_manager import connection_manager
from app.models.user import User, UserRole
from app.repositories.follow_repository import follow_repository
from app.services.conversation_service import conversation_service


@pytest.mark.asyncio
async def test_e2e_ws_live_message_push(db_session):
    u1 = User(email=f"wse1_{uuid.uuid4()}@ex.com", username=f"wse1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"wse2_{uuid.uuid4()}@ex.com", username=f"wse2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2])
    await db_session.commit()

    await follow_repository.create(db_session, u1.id, u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)

    # Register u2 as online via mock socket in connection_manager
    ws_u2 = AsyncMock()
    await connection_manager.connect(ws_u2, u2.id)
    assert connection_manager.is_user_online(u2.id) is True

    client_msg_id = str(uuid.uuid4())
    cmd_json = json.dumps({
        "v": 1,
        "cmd": "dm.send",
        "payload": {
            "conversation_id": str(conv.id),
            "client_msg_id": client_msg_id,
            "text": "Hello live over socket!",
        },
    })

    ws_u1 = AsyncMock()
    ws_u1.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=ws_u1, current_user=u1)
    finally:
        ws_module._db_override = None

    # 1. Verify ACK sent back to u1
    assert ws_u1.send_text.call_count == 1
    ack_data = json.loads(ws_u1.send_text.call_args[0][0])
    assert ack_data["v"] == 1
    assert ack_data["event"] == "ack"
    assert ack_data["payload"]["client_msg_id"] == client_msg_id

    # 2. Verify live dm.message pushed to u2!
    assert ws_u2.send_text.call_count == 1
    pushed_data = json.loads(ws_u2.send_text.call_args[0][0])
    assert pushed_data["v"] == 1
    assert pushed_data["event"] == "dm.message"
    assert pushed_data["payload"]["text"] == "Hello live over socket!"
    assert pushed_data["payload"]["sender_id"] == str(u1.id)

    connection_manager.disconnect(ws_u2, u2.id)

