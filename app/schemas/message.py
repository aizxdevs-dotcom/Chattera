from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.file import FileResponse  # ✅ reuse existing file schema


class MessageCreate(BaseModel):
    content: str
    conversation_id: str
    sender_id: str
    file_ids: Optional[List[str]] = []  # 🆕 optional multiple file attachments


class MessageResponse(BaseModel):
    message_id: str
    content: str
    timestamp: datetime
    sender_id: str
    conversation_id: str
    files: List[FileResponse] = []  # 🆕 return attached file metadata