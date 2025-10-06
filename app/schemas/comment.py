from pydantic import BaseModel
import datetime
from typing import Optional, List, Dict
from app.schemas.file import FileResponse


class CommentCreate(BaseModel):
    user_id: Optional[str] = None
    post_id: str
    description: Optional[str] = ""            # ✅ use description only
    file_ids: Optional[List[str]] = []         # ✅ optional multiple files


class CommentResponse(BaseModel):
    comment_id: str
    description: Optional[str] = None          # ✅ match your model
    created_at: datetime.datetime
    user_id: str
    post_id: str
    files: List[FileResponse] = []             # ✅ return file metadata
    reactions: Dict[str, int] = {}             # ✅ reaction counts
    current_user_reaction: Optional[str] = None # ✅ viewer’s reaction
    username: Optional[str] = None
    user_profile_url: Optional[str] = None