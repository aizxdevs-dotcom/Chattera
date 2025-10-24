"""
Email Service for OTP verification and password reset
Supports Gmail SMTP and follows best practices for email delivery
"""
import os
import random
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List

from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, 
    SMTP_FROM_EMAIL, SMTP_FROM_NAME
)


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
)

fm = FastMail(conf)


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
    
    await fm.send_message(message)


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
    
    await fm.send_message(message)


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
    
    await fm.send_message(message)
