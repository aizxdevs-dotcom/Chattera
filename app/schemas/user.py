from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
   

class UserResponse(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_photo: Optional[str] = None 
    is_verified: Optional[bool] = False  # Add verification status

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None

# Email verification schemas
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp_code: str  # 4-digit OTP

class ResendOTPRequest(BaseModel):
    email: EmailStr

# Password reset schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str  # 4-digit OTP
    new_password: str

# Delete account schema
class DeleteAccountRequest(BaseModel):
    password: str
    reason: Optional[str] = None  # Optional reason for deletion

# Update password schema
class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str
   