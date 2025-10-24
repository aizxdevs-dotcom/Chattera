from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class InvitationCreate(BaseModel):
    receiver_uid: str = Field(..., description="UID of the user to send friend request to")
    sender_uid: Optional[str] = Field(None, description="Sender UID (automatically set from token)")
    message: Optional[str] = Field(None, max_length=500, description="Optional message with friend request")

class InvitationResponse(BaseModel):
    sender_uid: str
    receiver_uid: str
    sender_username: Optional[str] = None
    receiver_username: Optional[str] = None
    sender_profile_photo: Optional[str] = None
    receiver_profile_photo: Optional[str] = None
    status: Literal["pending", "accepted", "declined"]
    message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class InvitationListResponse(BaseModel):
    invitations: list[InvitationResponse]
    total: int

class InvitationActionResponse(BaseModel):
    message: str
    sender_uid: str
    receiver_uid: str
    status: Literal["accepted", "declined"]