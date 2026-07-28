"""
Async Email delivery service.

Uses aiosmtplib to send non-blocking HTML/text emails for account verification and password reset.
If settings.EMAILS_ENABLED is False, emails are logged to stdout instead of being transmitted over SMTP.
Includes robust exception handling to ensure email failures do not crash API requests.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Asynchronously send an email using Resend API or SMTP.
    If RESEND_API_KEY is provided, dispatches via Resend HTTP REST API.
    If settings.EMAILS_ENABLED is False, emails are logged to stdout instead of being transmitted over SMTP.
    Catches network and API exceptions safely to avoid crashing API routes.
    """
    if settings.RESEND_API_KEY and not settings.RESEND_API_KEY.endswith("placeholder"):
        from_email = settings.SMTP_FROM_EMAIL or "onboarding@resend.dev"
        # Resend testing mode requires onboarding@resend.dev for public email providers
        if any(from_email.lower().endswith(domain) for domain in ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com")):
            from_email = "onboarding@resend.dev"
        from_name = settings.SMTP_FROM_NAME or settings.PROJECT_NAME
        from_header = f"{from_name} <{from_email}>"

        logger.info(f"[EMAIL DISPATCH] Attempting Resend API delivery to '{email_to}' (From: {from_header})...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": from_header,
                        "to": [email_to],
                        "subject": subject,
                        "html": html_content,
                    },
                    timeout=10.0,
                )
                if response.status_code in (200, 201):
                    res_data = response.json()
                    logger.info(f"[RESEND SUCCESS] Delivered email to {email_to} via Resend API (ID: {res_data.get('id')})")
                else:
                    logger.error(f"[RESEND ERROR] Failed to send email to {email_to}: Status {response.status_code} - {response.text}")
            return
        except Exception as exc:
            logger.error(f"[RESEND ERROR] Failed to transmit email to {email_to} via Resend API: {exc}")
            return

    if not settings.EMAILS_ENABLED:
        print(f"\n[MOCK EMAIL SERVICE] Email to: {email_to}")
        print(f"[MOCK EMAIL SERVICE] Subject: {subject}")
        print(f"[MOCK EMAIL SERVICE] Content Preview:\n{html_content[:300]}...\n")
        return

    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = email_to
    message["Subject"] = subject

    html_part = MIMEText(html_content, "html", "utf-8")
    message.attach(html_part)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Successfully sent email to {email_to}")
    except aiosmtplib.SMTPAuthenticationError:
        logger.error(f"[EMAIL ERROR] Invalid SMTP credentials for {settings.SMTP_USER}")
    except aiosmtplib.SMTPException as exc:
        logger.error(f"[EMAIL ERROR] SMTP error sending email to {email_to}: {exc}")
    except Exception as exc:
        logger.error(f"[EMAIL ERROR] Failed to send email to {email_to}: {exc}")


async def send_verification_email(email_to: str, token: str) -> None:
    """
    Send account email verification link.
    """
    subject = f"{settings.PROJECT_NAME} - Verify Your Account"
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4A90E2;">Welcome to {settings.PROJECT_NAME}!</h2>
            <p>Thank you for signing up. Please confirm your email address by clicking the button below:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Verify Email Address</a>
            </p>
            <p style="font-size: 12px; color: #777;">Or copy and paste this link into your browser:<br><a href="{verification_link}">{verification_link}</a></p>
            <p>If you did not create an account, please ignore this email.</p>
        </body>
    </html>
    """
    await send_email(email_to=email_to, subject=subject, html_content=html_content)


async def send_password_reset_email(email_to: str, token: str) -> None:
    """
    Send password reset token link.
    """
    subject = f"{settings.PROJECT_NAME} - Password Reset Request"
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #D0021B;">Password Reset Request</h2>
            <p>You requested a password reset for your account. Click the button below to set a new password:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #D0021B; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
            </p>
            <p style="font-size: 12px; color: #777;">Or copy and paste this link into your browser:<br><a href="{reset_link}">{reset_link}</a></p>
            <p><strong>This link is valid for 15 minutes.</strong></p>
            <p>If you did not request a password reset, please ignore this email and your password will remain unchanged.</p>
        </body>
    </html>
    """
    await send_email(email_to=email_to, subject=subject, html_content=html_content)
