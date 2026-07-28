"""
Unit tests for Webhook Idempotency & Error Resilience (Task 3.3).
"""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.asyncio
async def test_webhook_database_error_triggers_rollback():
    """Verify SQLAlchemyError triggers db.rollback and raises HTTP 500."""
    from app.services.billing_service import billing_service

    mock_db = AsyncMock()
    mock_db.execute.side_effect = SQLAlchemyError("Database connection lost")

    event = {
        "id": "evt_test_db_error",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_err",
                "customer": "cus_test_err",
            }
        },
    }

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.handle_webhook_event(db=mock_db, event=event)

    assert exc_info.value.status_code == 500
    mock_db.rollback.assert_called_once()
