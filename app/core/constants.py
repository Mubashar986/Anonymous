"""
Application-wide constants for the WebSocket chat feature.

This module has ZERO internal imports — it only uses the Python standard library.
Import freely from any layer without risk of circular imports.
"""

from enum import IntEnum, StrEnum


# Maximum Unicode character length for any single WebSocket message payload.
# Applies to both direct messages and room messages.
# Enforced at: Pydantic schema validation (ws.py) AND runtime handler check.
WS_MAX_TEXT_LEN: int = 4_000


class WSCloseCode(IntEnum):
    """
    WebSocket close codes sent by the server via websocket.close(code=...).

    Codes 4000–4999 are reserved for application use (RFC 6455 Section 7.4.2).
    Standard codes 1000 and 1011 are used per their defined semantics.

    React reconnect guidance (for Task 3.5):
    - NORMAL (1000):           Clean shutdown. Do NOT reconnect.
    - INVALID_TOKEN (4001):    Auth failed. Redirect to login. Do NOT reconnect.
    - ACCOUNT_INACTIVE (4003): Account disabled. Show error. Do NOT reconnect.
    - POLICY_VIOLATION (4008): Rate-limit or payload too large. May retry after backoff.
    - SERVER_ERROR (1011):     Unexpected error. Reconnect with exponential backoff.
    """
    NORMAL           = 1000
    INVALID_TOKEN    = 4001
    ACCOUNT_INACTIVE = 4003
    POLICY_VIOLATION = 4008
    SERVER_ERROR     = 1011


class WSErrorCode(StrEnum):
    """
    Application-level error codes sent inside a WSEvent(event='error') payload.

    These are NOT WebSocket close codes. They appear in the JSON body of an
    error event while the connection remains open.
    """
    INVALID_PAYLOAD     = "invalid_payload"
    UNKNOWN_COMMAND     = "unknown_command"
    PAYLOAD_TOO_LARGE   = "payload_too_large"
    FORBIDDEN           = "forbidden"
    CONVERSATION_LOCKED = "conversation_locked"
    ROOM_ACCESS_DENIED  = "room_access_denied"
    DUPLICATE_MESSAGE   = "duplicate_message"
