from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ContactResponse(BaseModel):
    uid: str
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_photo: Optional[str] = None
    friendship_since: Optional[str] = None

class ContactListResponse(BaseModel):
    contacts: list[ContactResponse]
    total: int

class ContactStatsResponse(BaseModel):
    total_friends: int
    pending_sent: int
    pending_received: int

class MutualFriendsResponse(BaseModel):
    mutual_friends: list[ContactResponse]
    count: int