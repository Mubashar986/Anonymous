"""
Pydantic schemas for the versioned WebSocket JSON envelope.

Authorization matrix reference:
  .agents/artifacts/realtime-chat/authorization_matrix.md

Protocol version: 1

Command envelope  (browser → server):  {"v": 1, "cmd": "<name>",   "payload": {...}}
Event envelope    (server → browser):  {"v": 1, "event": "<name>", "payload": {...}}
"""

import uuid
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field

from app.core.constants import WS_MAX_TEXT_LEN, WSCloseCode, WSErrorCode

# Re-export constants so consumers only need to import from app.schemas.ws
__all__ = [
    "WS_PROTOCOL_VERSION",
    "WS_MAX_TEXT_LEN",
    "WSCloseCode",
    "WSErrorCode",
    "WSCommandName",
    "WSEventName",
    "DmSendPayload",
    "RoomSendPayload",
    "WSCommand",
    "WSEvent",
    "WSErrorPayload",
    "WSAckPayload",
    "DmMessagePayload",
    "RoomMessagePayload",
    "NotificationCreatedPayload",
]

WS_PROTOCOL_VERSION: int = 1


# ---------------------------------------------------------------------------
# Command and event name enumerations
# ---------------------------------------------------------------------------

from enum import StrEnum


class WSCommandName(StrEnum):
    """All commands the browser may send to the server."""
    DM_SEND   = "dm.send"
    ROOM_SEND = "room.send"


class WSEventName(StrEnum):
    """All events the server may push to the browser."""
    DM_MESSAGE           = "dm.message"
    ROOM_MESSAGE         = "room.message"
    NOTIFICATION_CREATED = "notification.created"
    ERROR                = "error"
    ACK                  = "ack"


# ---------------------------------------------------------------------------
# Payload schemas — browser → server
# ---------------------------------------------------------------------------

_TextBody = Annotated[
    str,
    Field(
        min_length=1,
        max_length=WS_MAX_TEXT_LEN,
        description=f"Message text. Max {WS_MAX_TEXT_LEN} Unicode characters.",
    ),
]


class DmSendPayload(BaseModel):
    """Payload for the 'dm.send' command."""
    conversation_id: uuid.UUID
    client_msg_id: uuid.UUID = Field(
        description="Client-generated idempotency key. Reuse the same UUID to retry safely.",
    )
    text: _TextBody


class RoomSendPayload(BaseModel):
    """Payload for the 'room.send' command."""
    room_id: uuid.UUID
    client_msg_id: uuid.UUID = Field(
        description="Client-generated idempotency key.",
    )
    text: _TextBody


# ---------------------------------------------------------------------------
# Top-level command envelope (browser → server)
# ---------------------------------------------------------------------------

class WSCommand(BaseModel):
    """
    Top-level WebSocket command envelope.

    Handlers should discriminate on 'cmd' before parsing 'payload'
    into the specific payload schema (DmSendPayload, RoomSendPayload, …).
    """
    v: Literal[1] = 1
    cmd: WSCommandName
    payload: dict[str, Any]


# ---------------------------------------------------------------------------
# Payload schemas — server → browser
# ---------------------------------------------------------------------------

class DmMessagePayload(BaseModel):
    """Payload for the 'dm.message' event."""
    msg_id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    client_msg_id: uuid.UUID
    text: str
    timestamp: str  # ISO 8601 UTC string; avoids tz-naive datetime serialization issues


class RoomMessagePayload(BaseModel):
    """Payload for the 'room.message' event."""
    msg_id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    text: str
    timestamp: str  # ISO 8601 UTC string
    sender_username: Optional[str] = None


class NotificationCreatedPayload(BaseModel):
    """
    Payload for the 'notification.created' WebSocket event.
    Matches NotificationResponse structure so frontends can consume WebSocket
    events without nested vs flat property mismatches.
    """
    id: uuid.UUID
    recipient_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    event_type: str
    payload: dict[str, Any]
    is_read: bool = False
    created_at: str  # ISO 8601 UTC string


class WSErrorPayload(BaseModel):
    """Payload for the 'error' event (connection stays open)."""
    code: WSErrorCode
    detail: str


class WSAckPayload(BaseModel):
    """Payload for the 'ack' event (message successfully persisted)."""
    client_msg_id: uuid.UUID
    msg_id: uuid.UUID
    status: Literal["ok"] = "ok"


# ---------------------------------------------------------------------------
# Top-level event envelope (server → browser)
# ---------------------------------------------------------------------------

class WSEvent(BaseModel):
    """
    Top-level WebSocket event envelope.

    Build events using the class-method helpers rather than raw dicts to keep
    the protocol version field consistent across all send sites.
    """
    v: Literal[1] = 1
    event: WSEventName
    payload: dict[str, Any]

    @classmethod
    def error(cls, code: WSErrorCode, detail: str) -> "WSEvent":
        """Convenience constructor for error events."""
        return cls(
            event=WSEventName.ERROR,
            payload=WSErrorPayload(code=code, detail=detail).model_dump(),
        )

    @classmethod
    def ack(cls, client_msg_id: uuid.UUID, msg_id: uuid.UUID) -> "WSEvent":
        """Convenience constructor for acknowledgement events."""
        return cls(
            event=WSEventName.ACK,
            payload=WSAckPayload(
                client_msg_id=client_msg_id, msg_id=msg_id
            ).model_dump(),
        )
