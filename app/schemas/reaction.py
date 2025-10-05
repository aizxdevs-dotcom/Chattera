from pydantic import BaseModel
from typing import Literal, Optional
import datetime

class ReactionCreate(BaseModel):
    post_id: str
    type: Literal["like", "haha", "sad", "angry", "care"]

class ReactionResponse(BaseModel):
    reaction_id: str
    type: str
    created_at: datetime.datetime
    user_id: str
    post_id: str
    username: Optional[str] = None
    user_profile_url: Optional[str] = None