from fastapi import (
    APIRouter, HTTPException, Depends, UploadFile, File, status, Request, Security
)
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from uuid import uuid4, UUID
from datetime import timedelta
import hashlib, boto3, os
from dotenv import load_dotenv
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.hash import argon2

from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, UserUpdate,
    VerifyEmailRequest, ResendOTPRequest, 
    ForgotPasswordRequest, ResetPasswordRequest,
    DeleteAccountRequest, UpdatePasswordRequest
)
from app.crud.user import user_crud
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_access_token,
)
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
    generate_otp,
    get_otp_expiry,
)

router = APIRouter()

# -------------------------------------------------------------------------
# AWS S3 setup
# -------------------------------------------------------------------------
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")

# -------------------------------------------------------------------------
# Authentication helpers
# -------------------------------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(token = Security(bearer_scheme)) -> str:
    """Extract and validate the user ID from a JWT bearer token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = verify_access_token(token.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {e}",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return user_id

def hash_password(password: str) -> str:
    """Hash password securely with Argon2."""
    if len(password) > 72:
        password = hashlib.sha256(password.encode()).hexdigest()
    return argon2.hash(password)


def validate_password_strength(password: str):
    """Ensure password has at least 8 chars, one uppercase, one lowercase, one digit and one symbol."""
    import re
    pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
    if not pattern.match(password):
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must be at least 8 characters and include an uppercase letter, "
                "a lowercase letter, a number and a symbol."
            ),
        )

# -------------------------------------------------------------------------
# Registration (sends OTP email)
# -------------------------------------------------------------------------
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    existing_user = user_crud.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid4())
    password_hash = hash_password(user.password)
    # Validate password strength
    validate_password_strength(user.password)
    
    # Generate OTP for email verification
    otp_code = generate_otp()
    otp_expires_at = get_otp_expiry()

    try:
        db_user = user_crud.create_user(
            user_id, 
            user.username, 
            user.email, 
            password_hash,
            otp_code=otp_code,
            otp_expires_at=otp_expires_at
        )
        
        # Send verification email
        await send_verification_email(user.email, user.username, otp_code)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")

    return UserResponse(
        user_id=user_id, 
        username=user.username, 
        email=user.email,
        is_verified=False
    )

# -------------------------------------------------------------------------
# Login (requires email verification)
# -------------------------------------------------------------------------
@router.post("/login")
def login(user: UserLogin):
    db_user = user_crud.get_user_by_email(user.email)
    if not db_user or not argon2.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if email is verified
    if db_user.is_verified != "true":
        raise HTTPException(
            status_code=403, 
            detail="Email not verified. Please check your email for the verification code."
        )

    access_token = create_access_token({"sub": db_user.user_id})
    refresh_token = create_refresh_token({"sub": db_user.user_id})

    # Send access token in JSON; refresh token stored as HttpOnly cookie
    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,      # HTTPS required on Render
        samesite="Strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )
    return response

# -------------------------------------------------------------------------
# Email Verification
# -------------------------------------------------------------------------
@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify user's email using OTP code"""
    from datetime import datetime, timezone

    db_user = user_crud.get_user_by_email(request.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.is_verified == "true":
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Check if OTP exists and is valid
    if not db_user.otp_code:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")
    
    # Check if OTP has expired
    if db_user.otp_expires_at:
        otp_expires = db_user.otp_expires_at
        # normalize stored datetime to timezone-aware UTC if needed
        if getattr(otp_expires, "tzinfo", None) is None:
            otp_expires = otp_expires.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now > otp_expires:
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
    # Verify OTP code
    if db_user.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Mark user as verified and clear OTP
    user_crud.verify_user(db_user.user_id)
    
    # Send welcome email
    try:
        await send_welcome_email(db_user.email, db_user.username)
    except Exception as e:
        print(f"⚠️ Failed to send welcome email: {e}")
    
    return {"message": "Email verified successfully! You can now log in."}

# -------------------------------------------------------------------------
# Resend OTP
# -------------------------------------------------------------------------
@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest):
    """Resend OTP verification code to user's email"""
    db_user = user_crud.get_user_by_email(request.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.is_verified == "true":
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_expires_at = get_otp_expiry()
    
    # Update user with new OTP
    user_crud.update_otp(db_user.user_id, otp_code, otp_expires_at)
    
    # Send email
    try:
        await send_verification_email(db_user.email, db_user.username, otp_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
    
    return {"message": "OTP sent successfully. Please check your email."}

# -------------------------------------------------------------------------
# Forgot Password (sends reset OTP)
# -------------------------------------------------------------------------
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset OTP to user's email"""
    db_user = user_crud.get_user_by_email(request.email)
    if not db_user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a reset code has been sent."}
    
    # Generate reset OTP
    reset_token = generate_otp()
    reset_expires_at = get_otp_expiry()
    
    # Save reset token
    user_crud.update_reset_token(db_user.user_id, reset_token, reset_expires_at)
    
    # Send reset email
    try:
        await send_password_reset_email(db_user.email, db_user.username, reset_token)
    except Exception as e:
        print(f"⚠️ Failed to send reset email: {e}")
    
    return {"message": "If the email exists, a reset code has been sent."}

# -------------------------------------------------------------------------
# Reset Password (verifies OTP and updates password)
# -------------------------------------------------------------------------
@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    """Reset password using OTP code"""
    from datetime import datetime, timezone

    db_user = user_crud.get_user_by_email(request.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if reset token exists
    if not db_user.reset_token:
        raise HTTPException(status_code=400, detail="No reset code found. Please request a new one.")
    
    # Check if reset token has expired
    if db_user.reset_token_expires_at:
        reset_expires = db_user.reset_token_expires_at
        if getattr(reset_expires, "tzinfo", None) is None:
            reset_expires = reset_expires.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now > reset_expires:
            raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")
    
    # Verify reset token
    if db_user.reset_token != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Validate new password strength and hash
    validate_password_strength(request.new_password)
    new_password_hash = hash_password(request.new_password)
    user_crud.reset_user_password(db_user.user_id, new_password_hash)
    
    return {"message": "Password reset successfully! You can now log in with your new password."}

# -------------------------------------------------------------------------
# Secure profile update
# -------------------------------------------------------------------------
@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_profile(
    user_id: str,
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user),
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this profile")

    updated_user = user_crud.update_user(
        user_id,
        full_name=user_update.full_name,
        bio=user_update.bio,
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=str(updated_user.user_id),
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        bio=updated_user.bio,
    )

# -------------------------------------------------------------------------
# Upload profile photo
# -------------------------------------------------------------------------
@router.post("/users/{user_id}/upload-photo", response_model=UserResponse)
async def upload_profile_photo(
    user_id: UUID,
    file: UploadFile = File(..., description="Profile photo"),
    current_user_id: str = Depends(get_current_user),
):
    # ✅ Allow only self‑updates
    if str(user_id) != current_user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this photo")

    # ✅ Validate file type
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG files are allowed")

    # ✅ Use a unique, non‑colliding filename (user_id + random/uuid + timestamp)
    unique_suffix = uuid4().hex
    object_name = f"profile_photos/{user_id}_{unique_suffix}_{file.filename}"

    try:
        s3.upload_fileobj(
            file.file,
            bucket,
            object_name,
            ExtraArgs={"ContentType": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    # ✅ Cache‑busting public URL
    region = os.getenv("AWS_REGION")
    file_url = f"https://{bucket}.s3.{region}.amazonaws.com/{object_name}?v={unique_suffix}"

    # ✅ Update only this single user
    updated_user = user_crud.update_user(
        str(user_id),
        profile_photo=file_url,
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=updated_user.user_id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        bio=updated_user.bio,
        profile_photo=updated_user.profile_photo,
    )

# -------------------------------------------------------------------------
# Get current user's profile
# -------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user_id: str = Depends(get_current_user)):
    user = user_crud.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        bio=user.bio,
        profile_photo=user.profile_photo,
    )

# -------------------------------------------------------------------------
# Refresh access token
# -------------------------------------------------------------------------
@router.post("/refresh")
def refresh_access_token(
    request: Request,
    refresh_token: str | None = None,
):
    """Exchange a valid refresh token (cookie or body) for a new access token."""
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if not user_crud.get_user_by_id(user_id):
            raise HTTPException(status_code=401, detail="User not found")

        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access = create_access_token({"sub": user_id}, expires_delta=expires)
        return {"access_token": new_access, "token_type": "bearer"}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# -------------------------------------------------------------------------
# Get all users (for People You May Know)
# -------------------------------------------------------------------------
@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    limit: int = 50,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all users in the system for 'People You May Know'.
    Excludes the authenticated user from results.
    """
    try:
        users = user_crud.get_all_users(exclude_user_id=current_user_id, limit=limit)
        return [
            UserResponse(
                user_id=str(user["user_id"]),
                username=user["username"],
                email=user.get("email"),
                full_name=user.get("full_name"),
                bio=user.get("bio"),
                profile_photo=user.get("profile_photo")
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {e}")

# -------------------------------------------------------------------------
# Search users
# -------------------------------------------------------------------------
@router.get("/users/search", response_model=list[UserResponse])
def search_users(
    q: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user)
):
    """
    Search users by username or full name.
    Excludes the authenticated user from results.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters"
        )
    
    try:
        users = user_crud.search_users(q, exclude_user_id=current_user_id, limit=limit)
        return [
            UserResponse(
                user_id=user["user_id"],
                username=user["username"],
                email=user.get("email"),
                full_name=user.get("full_name"),
                bio=user.get("bio"),
                profile_photo=user.get("profile_photo")
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

# -------------------------------------------------------------------------
# Delete account (requires password verification)
# -------------------------------------------------------------------------
@router.delete("/users/{user_id}/delete")
def delete_account(
    user_id: str,
    request: DeleteAccountRequest,
    current_user_id: str = Depends(get_current_user),
):
    """
    Delete user account after password verification.
    Accepts optional reason for deletion.
    """
    # Ensure user can only delete their own account
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    
    # Get user and verify password
    db_user = user_crud.get_user_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify password
    if not argon2.verify(request.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Log deletion reason if provided (optional: save to separate log/table)
    if request.reason:
        print(f"[Account Deletion] User {user_id} ({db_user.email}): {request.reason}")
    
    # Delete the user
    success = user_crud.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete account. Please try again."
        )
    
    return {"detail": "Account deleted successfully"}

# -------------------------------------------------------------------------
# Update password (requires current password verification)
# -------------------------------------------------------------------------
@router.put("/users/{user_id}/password")
def update_password(
    user_id: str,
    request: UpdatePasswordRequest,
    current_user_id: str = Depends(get_current_user),
):
    """
    Update user password after verifying current password.
    """
    # Ensure user can only update their own password
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own password"
        )
    
    # Get user and verify current password
    db_user = user_crud.get_user_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not argon2.verify(request.current_password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password length
    # Validate new password strength
    validate_password_strength(request.new_password)
    
    # Hash and update password
    new_hash = hash_password(request.new_password)
    db_user.password_hash = new_hash
    db_user.save()
    
    return {"detail": "Password updated successfully"}