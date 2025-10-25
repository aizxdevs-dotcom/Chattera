"""
Email Service for OTP verification and password reset
Supports Gmail SMTP and follows best practices for email delivery
"""
import os
import random
import logging
from datetime import datetime, timedelta
# avoid dependency on pydantic for simple typing here
from typing import List, Optional

from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME,
)

# Use SendGrid API via stdlib provider (no httpx)
from app.services.mail_api_provider import send_email_async


async def _send_via_sendgrid_only(
    to_email: str, subject: str, html_body: str, from_email: Optional[str] = None, timeout: int = 15
) -> bool:
    """Send email via SendGrid API (stdlib). Returns True on success."""
    try:
        ok, status, body = await send_email_async(to_email, subject, html_body, from_email, timeout)
        if ok:
            logging.info("Email sent via SendGrid to %s (status=%s)", to_email, status)
            return True
        logging.error("SendGrid API returned non-success for %s: %s - %s", to_email, status, (body[:200] if isinstance(body, (bytes, bytearray)) else body))
        return False
    except Exception as exc:
        logging.exception("SendGrid send failed for %s: %s", to_email, exc)
        return False


def generate_otp() -> str:
    """Generate a 4-digit OTP code as a zero-padded string."""
    return f"{random.randint(0, 9999):04d}"


def get_otp_expiry() -> datetime:
    """Get OTP expiry time (10 minutes from now)"""
    return datetime.utcnow() + timedelta(minutes=10)


async def send_verification_email(email: str, username: str, otp_code: str):
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
    
    subject = "🔐 Verify Your Email - Soceyo"
    sent = await _send_via_sendgrid_only(email, subject, html_content)
    if not sent:
        raise Exception("Failed to send verification email via SendGrid")


async def send_password_reset_email(email: str, username: str, otp_code: str):
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
    
    subject = "🔐 Reset Your Password - Soceyo"
    sent = await _send_via_sendgrid_only(email, subject, html_content)
    if not sent:
        raise Exception("Failed to send password reset email via SendGrid")


async def send_welcome_email(email: str, username: str):
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
    
    subject = "🎉 Welcome to Soceyo!"
    sent = await _send_via_sendgrid_only(email, subject, html_content)
    if not sent:
        raise Exception("Failed to send welcome email via SendGrid")
