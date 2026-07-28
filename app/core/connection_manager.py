"""
In-Memory Realtime WebSocket Connection Manager.
"""

import json
import logging
import uuid
from typing import Dict, Set, Union
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections mapped by user_id.
    Supports multi-device / multi-tab connections per user.
    """

    def __init__(self):
        self.active_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """
        Accept socket connection and register under user_id.
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Active sockets: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """
        Deregister socket for user_id. Cleans up empty user sets.
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        """
        Check if user_id has at least one active WebSocket connection.
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_personal_message(self, data: Union[dict, str], user_id: uuid.UUID) -> None:
        """
        Send JSON message to all active WebSocket connections belonging to user_id.
        """
        if user_id not in self.active_connections:
            return

        payload = json.dumps(data) if isinstance(data, dict) else data
        dead_sockets = set()

        for websocket in list(self.active_connections[user_id]):
            try:
                await websocket.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending payload to socket for user {user_id}: {e}")
                dead_sockets.add(websocket)

        # Clean up dead sockets
        for dead_ws in dead_sockets:
            self.disconnect(dead_ws, user_id)

    async def broadcast(self, data: Union[dict, str]) -> None:
        """
        Broadcast JSON message to all connected users across the application.
        """
        payload = json.dumps(data) if isinstance(data, dict) else data
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(payload, user_id)


connection_manager = ConnectionManager()
