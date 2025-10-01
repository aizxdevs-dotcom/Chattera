from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.crud.user import user_crud
from passlib.hash import argon2
from uuid import uuid4
from fastapi.security import OAuth2PasswordBearer
from app.config import create_access_token, verify_access_token
import hashlib

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    # Preprocess passwords longer than 72 characters
    if len(password) > 72:
        password = hashlib.sha256(password.encode()).hexdigest()
    return argon2.hash(password)

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate):
    existing_user = user_crud.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email registered")

    user_id = str(uuid4())
    password_hash = hash_password(user.password)
    try:
        user_crud.create_user(user_id, user.username, user.email, password_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return UserResponse(user_id=user_id, username=user.username, email=user.email)

@router.post("/login")
def login_user(user: UserLogin):
    db_user = user_crud.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_hash = db_user.password_hash  # Access attribute directly
    if not argon2.verify(user.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}

@router.post("/token")
def generate_token(user: UserLogin):
    db_user = user_crud.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_hash = db_user.password_hash  # Access attribute directly
    if not argon2.verify(user.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.user_id})  # Access attribute directly
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]