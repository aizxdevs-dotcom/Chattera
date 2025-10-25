"""
Email Service for OTP verification and password reset
Supports Gmail SMTP and follows best practices for email delivery
"""
import os
import random
import logging
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List, Tuple, Optional
import json
import urllib.request
import urllib.error
import asyncio

from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, 
    SMTP_FROM_EMAIL, SMTP_FROM_NAME
)

# Optional SendGrid configuration (HTTP API)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", SMTP_FROM_EMAIL)
SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


# FastAPI-Mail Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=SMTP_USERNAME,
    MAIL_PASSWORD=SMTP_PASSWORD,
    MAIL_FROM=SMTP_FROM_EMAIL,
    MAIL_PORT=SMTP_PORT,
    MAIL_SERVER=SMTP_HOST,
    MAIL_FROM_NAME=SMTP_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TIMEOUT=int(os.getenv("SMTP_TIMEOUT", 15)),
)

fm = FastMail(conf)


async def _send_message_with_fallback(message: MessageSchema) -> bool:
    """Try sending with the primary config, and fall back to SSL(465) if STARTTLS fails (common with Gmail)."""
    try:
        await fm.send_message(message)
        return True
    except Exception as exc:
        logging.exception("⚠️ Failed to send email with primary SMTP (%s:%s): %s", SMTP_HOST, SMTP_PORT, exc)

        # If primary is gmail STARTTLS on 587, try SSL on 465 as a fallback
        try_ssl_fallback = SMTP_HOST and ("gmail" in SMTP_HOST.lower() or "smtp.gmail.com" in SMTP_HOST.lower()) and SMTP_PORT == 587
        if try_ssl_fallback:
            logging.info("Attempting SSL fallback to smtp.gmail.com:465")
            try:
                alt_conf = ConnectionConfig(
                    MAIL_USERNAME=SMTP_USERNAME,
                    MAIL_PASSWORD=SMTP_PASSWORD,
                    MAIL_FROM=SMTP_FROM_EMAIL,
                    MAIL_PORT=465,
                    MAIL_SERVER=SMTP_HOST,
                    MAIL_FROM_NAME=SMTP_FROM_NAME,
                    MAIL_STARTTLS=False,
                    MAIL_SSL_TLS=True,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=True,
                    TIMEOUT=int(os.getenv("SMTP_TIMEOUT", 15)),
                )
                alt_fm = FastMail(alt_conf)
                await alt_fm.send_message(message)
                logging.info("✅ Email sent via SSL fallback (smtp.gmail.com:465)")
                return True
            except Exception as exc2:
                logging.exception("⚠️ SSL fallback also failed: %s", exc2)

        # If SMTP attempts failed and SendGrid is configured, try SendGrid HTTP API as a fallback
        if SENDGRID_API_KEY:
            logging.info("Attempting SendGrid HTTP API fallback")
            try:
                ok = await _send_via_sendgrid(message)
                if ok:
                    logging.info("✅ Email sent via SendGrid HTTP API")
                    return True
            except Exception as exc3:
                logging.exception("⚠️ SendGrid fallback failed: %s", exc3)

        # If we reached here, all attempts failed
        return False
        """Send the message using SendGrid first (if configured), then SMTP with optional SSL fallback.

        Order of attempts:
          1. SendGrid HTTP API (if SENDGRID_API_KEY provided)
          2. Primary SMTP via FastMail (configured `conf`)
          3. SSL SMTP fallback on port 465 (common fallback for Gmail)

        Returns True on first successful send, False if all methods fail.
        """

        # 1) Try SendGrid first when available (preferred in many PaaS environments)
        if SENDGRID_API_KEY:
            try:
                logging.info("Attempting to send email via SendGrid HTTP API (primary)")
                ok = await _send_via_sendgrid(message)
                if ok:
                    logging.info("✅ Email sent via SendGrid HTTP API (primary)")
                    return True
                logging.warning("SendGrid HTTP API returned non-success; falling back to SMTP")
            except Exception as exc:
                logging.exception("⚠️ SendGrid primary attempt raised an exception: %s", exc)

        # 2) Try primary SMTP via FastMail
        try:
            await fm.send_message(message)
            logging.info("✅ Email sent via primary SMTP (%s:%s)", SMTP_HOST, SMTP_PORT)
            return True
        except Exception as exc:
            logging.exception("⚠️ Failed to send email with primary SMTP (%s:%s): %s", SMTP_HOST, SMTP_PORT, exc)

        # 3) If primary is gmail STARTTLS on 587, try SSL on 465 as a fallback
        try_ssl_fallback = SMTP_HOST and ("gmail" in SMTP_HOST.lower() or "smtp.gmail.com" in SMTP_HOST.lower()) and SMTP_PORT == 587
        if try_ssl_fallback:
            logging.info("Attempting SSL fallback to smtp.gmail.com:465")
            try:
                alt_conf = ConnectionConfig(
                    MAIL_USERNAME=SMTP_USERNAME,
                    MAIL_PASSWORD=SMTP_PASSWORD,
                    MAIL_FROM=SMTP_FROM_EMAIL,
                    MAIL_PORT=465,
                    MAIL_SERVER=SMTP_HOST,
                    MAIL_FROM_NAME=SMTP_FROM_NAME,
                    MAIL_STARTTLS=False,
                    MAIL_SSL_TLS=True,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=True,
                    TIMEOUT=int(os.getenv("SMTP_TIMEOUT", 15)),
                )
                alt_fm = FastMail(alt_conf)
                await alt_fm.send_message(message)
                logging.info("✅ Email sent via SSL fallback (smtp.gmail.com:465)")
                return True
            except Exception as exc2:
                logging.exception("⚠️ SSL fallback also failed: %s", exc2)

        # All attempts failed
        logging.error("All email send attempts failed (SendGrid + SMTP + SSL fallback)")
        return False


async def _send_via_sendgrid(message: MessageSchema) -> bool:
    """Send the message via SendGrid using the stdlib (runs in threadpool). Returns True on success."""
    if not SENDGRID_API_KEY:
        return False

    subject = getattr(message, "subject", "")
    recipients = getattr(message, "recipients", []) or []
    body = getattr(message, "body", "")

    if not recipients:
        logging.warning("No recipients for SendGrid send")
        return False

    to_email = recipients[0]

    try:
        status, resp_body = await send_via_sendgrid_async(to_email, subject, body, SENDGRID_FROM_EMAIL)
        if 200 <= status < 300:
            return True
        logging.error("SendGrid API returned %s: %s", status, resp_body)
        return False
    except Exception as exc:
        logging.exception("SendGrid send failed (exception): %s", exc)
        return False


def _send_via_sendgrid_sync(to_email: str, subject: str, html_body: str, from_email: str) -> Tuple[int, str]:
    """Blocking send to SendGrid using urllib. Returns (status_code, response_body)."""
    payload = {
        "personalizations": [{
            "to": [{"email": to_email}]
        }],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(SENDGRID_SEND_URL, data=data, headers=headers, method="POST")
    timeout = int(os.getenv("SENDGRID_TIMEOUT", 15))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="ignore")
            return status, body
    except urllib.error.HTTPError as he:
        try:
            body = he.read().decode("utf-8", errors="ignore")
        except Exception:
            body = str(he)
        return getattr(he, "code", 500), body
    except Exception as exc:
        # re-raise to be handled by caller async wrapper
        raise


async def send_via_sendgrid_async(to_email: str, subject: str, html_body: str, from_email: str) -> Tuple[int, str]:
    """Async wrapper that runs the blocking urllib SendGrid call in a threadpool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_via_sendgrid_sync, to_email, subject, html_body, from_email)


def generate_otp() -> str:
    """Generate a 4-digit OTP code"""
    return str(random.randint(1000, 9999))


def get_otp_expiry() -> datetime:
    """Get OTP expiry time (10 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=10)


async def send_verification_email(email: EmailStr, username: str, otp_code: str):
    """Send email verification OTP to user"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f7;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .otp-box {{
                background: #f8f9fa;
                border: 2px dashed #667eea;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✉️ Email Verification</h1>
            </div>
            <div class="content">
                <h2>Hi {username}! 👋</h2>
                <p>Thank you for registering with Soceyo. To complete your registration, please verify your email address using the OTP code below:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #666; font-size: 14px;">Your verification code:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">This code will expire in 10 minutes</p>
                </div>
                
                <p>If you didn't request this verification, you can safely ignore this email.</p>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    Best regards,<br>
                    <strong>The Soceyo Team</strong>
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.utcnow().year} Soceyo. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="🔐 Verify Your Email - Soceyo",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    sent = await _send_message_with_fallback(message)
    if not sent:
        raise Exception("Failed to send verification email: SMTP connection failed or timed out")


async def send_password_reset_email(email: EmailStr, username: str, otp_code: str):
    """Send password reset OTP to user"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f7;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .otp-box {{
                background: #fff5f5;
                border: 2px dashed #f5576c;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 36px;
                font-weight: bold;
                color: #f5576c;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .warning {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hi {username}! 👋</h2>
                <p>We received a request to reset your password. Use the OTP code below to continue:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #666; font-size: 14px;">Your reset code:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">This code will expire in 10 minutes</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <p style="margin: 5px 0 0 0;">If you didn't request a password reset, please ignore this email and ensure your account is secure.</p>
                </div>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    Best regards,<br>
                    <strong>The Soceyo Team</strong>
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.utcnow().year} Soceyo. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="🔐 Reset Your Password - Soceyo",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    sent = await _send_message_with_fallback(message)
    if not sent:
        raise Exception("Failed to send password reset email: SMTP connection failed or timed out")


async def send_welcome_email(email: EmailStr, username: str):
    """Send welcome email after successful verification"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f7;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                background: #43e97b;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to Soceyo!</h1>
            </div>
            <div class="content">
                <h2>Hi {username}! 👋</h2>
                <p>Your email has been successfully verified! Welcome to the Soceyo community.</p>
                
                <p>You can now:</p>
                <ul>
                    <li>📝 Create and share posts</li>
                    <li>💬 Message friends in real-time</li>
                    <li>👥 Connect with people you may know</li>
                    <li>❤️ React and comment on posts</li>
                </ul>
                
                <p style="text-align: center;">
                    <a href="https://soceyo.vercel.app/login" class="btn">Start Exploring</a>
                </p>
                
                <p style="margin-top: 30px; color: #666; font-size: 14px;">
                    Best regards,<br>
                    <strong>The Soceyo Team</strong>
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.utcnow().year} Soceyo. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="🎉 Welcome to Soceyo!",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    sent = await _send_message_with_fallback(message)
    if not sent:
        raise Exception("Failed to send welcome email: SMTP connection failed or timed out")
