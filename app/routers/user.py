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

from app.schemas.user import UserCreate, UserResponse, UserLogin, UserUpdate
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

# -------------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------------
@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate):
    existing_user = user_crud.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid4())
    password_hash = hash_password(user.password)

    try:
        user_crud.create_user(user_id, user.username, user.email, password_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return UserResponse(user_id=user_id, username=user.username, email=user.email)

# -------------------------------------------------------------------------
# Login
# -------------------------------------------------------------------------
@router.post("/login")
def login(user: UserLogin):
    db_user = user_crud.get_user_by_email(user.email)
    if not db_user or not argon2.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

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