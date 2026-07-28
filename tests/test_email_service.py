"""
Unit tests for Core Email Delivery Module & Resend API Integration (Task 7.2).
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.core.email import send_email


@pytest.mark.asyncio
async def test_send_email_console_mock(capsys, monkeypatch):
    """Verify send_email prints to stdout when RESEND_API_KEY is unset and EMAILS_ENABLED is False."""
    monkeypatch.setattr("app.core.email.settings.RESEND_API_KEY", None)
    monkeypatch.setattr("app.core.email.settings.EMAILS_ENABLED", False)

    await send_email(
        email_to="mock@example.com",
        subject="Test Subject",
        html_content="<p>Test Content</p>",
    )

    captured = capsys.readouterr()
    assert "[MOCK EMAIL SERVICE]" in captured.out
    assert "mock@example.com" in captured.out


@pytest.mark.asyncio
async def test_send_email_resend_api_success(monkeypatch):
    """Verify send_email dispatches POST request to Resend API when RESEND_API_KEY is configured."""
    monkeypatch.setattr("app.core.email.settings.RESEND_API_KEY", "re_test_key_123")
    monkeypatch.setattr("app.core.email.settings.SMTP_FROM_EMAIL", "test@example.com")
    monkeypatch.setattr("app.core.email.settings.SMTP_FROM_NAME", "Test App")

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        await send_email(
            email_to="recipient@example.com",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        mock_post.assert_called_once()
        kwargs = mock_post.call_args.kwargs
        assert kwargs["headers"]["Authorization"] == "Bearer re_test_key_123"
        assert kwargs["json"]["to"] == ["recipient@example.com"]
        assert kwargs["json"]["subject"] == "Welcome!"
