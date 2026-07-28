"""
WebSocket Authentication and Session Adapter Dependency.
"""

import logging
import uuid
from typing import Optional
from fastapi import Depends, Query, WebSocket, WebSocketException
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.constants import WSCloseCode
from app.core.security import decode_token
from app.database.database import get_db
from app.models.user import User
from app.repositories.user_repository import user_repository

logger = logging.getLogger(__name__)


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate WebSocket connection via query parameter token.
    If unauthenticated or inactive, raises WebSocketException with WSCloseCode.INVALID_TOKEN (4001).
    FastAPI / Starlette automatically closes socket with specified close code.
    """
    if not token:
        logger.warning("WebSocket connection attempt missing token query parameter")
        raise WebSocketException(code=WSCloseCode.INVALID_TOKEN, reason="Missing token")

    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise WebSocketException(code=WSCloseCode.INVALID_TOKEN, reason="Invalid token")
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning(f"WebSocket token validation failed: {e}")
        raise WebSocketException(code=WSCloseCode.INVALID_TOKEN, reason="Invalid token")

    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        logger.warning(f"WebSocket auth failed: user {user_id} not found or inactive")
        raise WebSocketException(code=WSCloseCode.ACCOUNT_INACTIVE, reason="User inactive")

    return user
