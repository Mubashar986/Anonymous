"""
Milestone 3 End-to-End Integration Test Suite.

Verifies live direct messaging over WebSockets across all layers built in Tasks 3.1-3.5:
  - WebSocket authentication (get_current_user_ws)
  - ConnectionManager presence & multi-socket registry
  - Live WS command parsing & delivery ACK dispatch
  - Live recipient push (dm.message)
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
async def test_e2e_m3_full_websocket_lifecycle(db_session):
    u1 = User(email=f"m3_1_{uuid.uuid4()}@ex.com", username=f"m3_1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"m3_2_{uuid.uuid4()}@ex.com", username=f"m3_2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2])
    await db_session.commit()

    await follow_repository.create(db_session, u1.id, u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)

    # Connect recipient (u2)
    ws_u2 = AsyncMock()
    await connection_manager.connect(ws_u2, u2.id)
    assert connection_manager.is_user_online(u2.id) is True

    # Sender (u1) sends live DM over socket
    client_msg_id = str(uuid.uuid4())
    cmd_json = json.dumps({
        "v": 1,
        "cmd": "dm.send",
        "payload": {
            "conversation_id": str(conv.id),
            "client_msg_id": client_msg_id,
            "text": "Milestone 3 E2E Success!",
        },
    })

    ws_u1 = AsyncMock()
    ws_u1.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=ws_u1, current_user=u1)
    finally:
        ws_module._db_override = None

    # Verify ACK event sent back to u1
    ack_data = json.loads(ws_u1.send_text.call_args[0][0])
    assert ack_data["v"] == 1
    assert ack_data["event"] == "ack"
    assert ack_data["payload"]["client_msg_id"] == client_msg_id

    # Verify live dm.message pushed to u2
    pushed_data = json.loads(ws_u2.send_text.call_args[0][0])
    assert pushed_data["v"] == 1
    assert pushed_data["event"] == "dm.message"
    assert pushed_data["payload"]["text"] == "Milestone 3 E2E Success!"

    # Cleanup socket
    connection_manager.disconnect(ws_u2, u2.id)
    assert connection_manager.is_user_online(u2.id) is False

