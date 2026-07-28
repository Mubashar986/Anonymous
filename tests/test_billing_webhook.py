"""
Unit tests for Stripe Webhook Endpoint & Signature Verification (Task 3.1).
"""

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_webhook_missing_signature_header(monkeypatch):
    """Verify process_webhook raises HTTP 400 when signature header is empty/missing."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: True)
    monkeypatch.setattr("app.services.billing_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_test_secret_123")
    from app.services.billing_service import billing_service

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.process_webhook(payload_bytes=b"{}", sig_header="")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_webhook_unconfigured_secret(monkeypatch):
    """Verify process_webhook raises HTTP 503 when Stripe webhook secret is placeholder."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: True)
    monkeypatch.setattr("app.services.billing_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
    from app.services.billing_service import billing_service

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.process_webhook(payload_bytes=b"{}", sig_header="t=123,v1=abc")
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_webhook_invalid_signature(monkeypatch):
    """Verify process_webhook raises HTTP 400 when signature verification fails."""
    monkeypatch.setattr("app.services.billing_service.is_stripe_configured", lambda: True)
    monkeypatch.setattr("app.services.billing_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_test_secret_123")
    from app.services.billing_service import billing_service

    with pytest.raises(HTTPException) as exc_info:
        await billing_service.process_webhook(
            payload_bytes=b'{"id": "evt_test", "type": "checkout.session.completed"}',
            sig_header="t=1672531199,v1=invalid_signature_hash"
        )
    assert exc_info.value.status_code == 400
