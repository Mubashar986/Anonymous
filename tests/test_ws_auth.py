"""
Pytest unit tests for WebSocket authentication adapter.
"""

import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocketException

from app.core.constants import WSCloseCode
from app.core.security import create_access_token
from app.dependencies.ws_auth import get_current_user_ws
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_ws_auth_valid_token(db_session):
    u = User(email=f"ws_auth_{uuid.uuid4()}@ex.com", username=f"ws_{str(uuid.uuid4())[:8]}", hashed_password="x", role=UserRole.USER, is_active=True)
    db_session.add(u)
    await db_session.commit()

    token = create_access_token(subject=str(u.id))
    mock_ws = AsyncMock()

    user = await get_current_user_ws(websocket=mock_ws, token=token, db=db_session)
    assert user.id == u.id
    assert user.username == u.username


@pytest.mark.asyncio
async def test_ws_auth_missing_token(db_session):
    mock_ws = AsyncMock()
    with pytest.raises(WebSocketException) as exc_info:
        await get_current_user_ws(websocket=mock_ws, token=None, db=db_session)
    assert exc_info.value.code == WSCloseCode.INVALID_TOKEN
