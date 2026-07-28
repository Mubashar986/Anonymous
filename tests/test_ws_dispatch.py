"""
Pytest unit tests for live WebSocket message dispatch & ACKs.
"""

import json
import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocketDisconnect

from app.api.v1 import ws as ws_module
from app.api.v1.ws import websocket_endpoint
from app.models.user import User, UserRole
from app.repositories.follow_repository import follow_repository
from app.services.conversation_service import conversation_service


@pytest.mark.asyncio
async def test_ws_send_message_ack_flow(db_session):
    u1 = User(email=f"ws1_{uuid.uuid4()}@ex.com", username=f"ws1_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    u2 = User(email=f"ws2_{uuid.uuid4()}@ex.com", username=f"ws2_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add_all([u1, u2])
    await db_session.commit()

    await follow_repository.create(db_session, u1.id, u2.id)
    conv = await conversation_service.start_conversation(db_session, u1, u2.id)

    client_msg_id = str(uuid.uuid4())
    cmd_json = json.dumps({
        "v": 1,
        "cmd": "dm.send",
        "payload": {
            "conversation_id": str(conv.id),
            "client_msg_id": client_msg_id,
            "text": "Live WS Hello!",
        },
    })

    mock_ws = AsyncMock()
    mock_ws.receive_text.side_effect = [cmd_json, WebSocketDisconnect(code=1000)]

    ws_module._db_override = db_session
    try:
        await websocket_endpoint(websocket=mock_ws, current_user=u1)
    finally:
        ws_module._db_override = None

    assert mock_ws.send_text.call_count == 1
    sent_payload = json.loads(mock_ws.send_text.call_args[0][0])
    assert sent_payload["v"] == 1
    assert sent_payload["event"] == "ack"
    assert sent_payload["payload"]["client_msg_id"] == client_msg_id
    assert sent_payload["payload"]["status"] == "ok"

