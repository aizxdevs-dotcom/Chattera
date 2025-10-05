from pydantic import BaseModel, Field
from typing import List, Optional


class ConversationCreate(BaseModel):
    is_group: bool
    member_ids: List[str] = Field(..., min_items=1)


class ConversationMember(BaseModel):
    user_id: str
    username: Optional[str] = None
    user_profile_url: Optional[str] = None
    is_active: Optional[bool] = False   # 👈 new field


class ConversationResponse(BaseModel):
    conversation_id: str
    is_group: bool
    members: List[ConversationMember]