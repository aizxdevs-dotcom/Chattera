from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    conversation_id: str
    sender_id: str

class MessageResponse(BaseModel):
    message_id: str
    content: str
    timestamp: datetime
    sender_id: str
    conversation_id: str