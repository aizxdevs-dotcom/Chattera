from pydantic import BaseModel
from typing import Optional,List
import datetime
from app.schemas.file import FileResponse 

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

class FeedPostResponse(PostResponse):
    username: str
    email: str