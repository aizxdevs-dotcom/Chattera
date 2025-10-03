from pydantic import BaseModel
from typing import Optional

class FileCreate(BaseModel):
    url: str
    file_type: str
    size: int
    message_id: Optional[str] = None

class FileUpdate(BaseModel):
    url: Optional[str] = None
    file_type: Optional[str] = None
    size: Optional[int] = None

class FileResponse(BaseModel):
    file_id: str
    url: str
    file_type: str
    size: int