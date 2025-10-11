from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NotificationBase(BaseModel):
    receiver_id: str
    sender_id: str
    post_id: str
    type: str  # 'like' or 'comment'
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    notification_id: str
    created_at: datetime
    is_read: bool = False

    # 💡 These fields provide richer sender and post summary info
    sender_username: Optional[str] = None
    sender_profile_photo_url: Optional[str] = None
    post_description: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ updated for Pydantic v2
