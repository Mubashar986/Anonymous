"""
Pytest unit tests for ConnectionManager.
"""

import uuid
import pytest
from unittest.mock import AsyncMock
from app.core.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager_lifecycle():
    mgr = ConnectionManager()
    u1 = uuid.uuid4()

    ws1 = AsyncMock()
    ws2 = AsyncMock()

    assert mgr.is_user_online(u1) is False

    # Connect socket 1
    await mgr.connect(ws1, u1)
    assert mgr.is_user_online(u1) is True

    # Connect socket 2
    await mgr.connect(ws2, u1)
    assert len(mgr.active_connections[u1]) == 2

    # Send personal message
    await mgr.send_personal_message({"type": "test"}, u1)
    ws1.send_text.assert_called_once()
    ws2.send_text.assert_called_once()

    # Disconnect socket 1
    mgr.disconnect(ws1, u1)
    assert mgr.is_user_online(u1) is True

    # Disconnect socket 2 -> User goes offline
    mgr.disconnect(ws2, u1)
    assert mgr.is_user_online(u1) is False
