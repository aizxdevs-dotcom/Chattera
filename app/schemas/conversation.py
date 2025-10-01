from pydantic import BaseModel, Field
from typing import List

class ConversationCreate(BaseModel):
    is_group: bool
    member_ids: List[str] = Field(..., min_items=1)  # Renamed to match `member_ids` in CRUD and added validation

class ConversationResponse(BaseModel):
    conversation_id: str
    is_group: bool
    member_ids: List[str]  # Renamed to match `member_ids` in CRUD