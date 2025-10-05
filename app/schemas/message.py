from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.file import FileResponse  # reuse existing schema


class MessageCreate(BaseModel):
    conversation_id: str
    content: Optional[str] = None              # ✅ allow empty for file‑only
    file_ids: Optional[List[str]] = []         # optional multiple attachments


class MessageResponse(BaseModel):
    message_id: str
    content: Optional[str] = None
    timestamp: datetime
    sender_id: str
    username: Optional[str] = None             # ✅ for display
    user_profile_url: Optional[str] = None     # ✅ show avatar
    conversation_id: str
    files: List[FileResponse] = []