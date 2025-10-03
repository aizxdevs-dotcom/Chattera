from pydantic import BaseModel
from typing import Optional,List,Dict
import datetime
from app.schemas.file import FileResponse 
from app.schemas.comment import CommentResponse

class PostCreate(BaseModel):
    user_id: str                    # the author of the post
    description: Optional[str] = "" # 🆕 optional description
    file_ids: Optional[List[str]] = []  # 🆕 multiple attached file IDs

class PostUpdate(BaseModel):
    description: Optional[str] = None
    file_ids: Optional[List[str]] = None

class PostResponse(BaseModel):
    post_id: str
    description: Optional[str] = None
    created_at: datetime.datetime
    user_id: str
    files: List[FileResponse] = []  # 🆕 return metadata for attached files
    comments: List[CommentResponse] = [] 
    reactions: Dict[str, int] = {}
    current_user_reaction: Optional[str] = None

class FeedPostResponse(PostResponse):
    username: str
    email: str