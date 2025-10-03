from pydantic import BaseModel
import datetime
from typing import Optional

class CommentCreate(BaseModel):
    user_id: str
    post_id: str
    text: str

class CommentResponse(BaseModel):
    comment_id: str
    text: str
    created_at: datetime.datetime
    user_id: str
    post_id: str