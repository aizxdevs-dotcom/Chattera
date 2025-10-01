from pydantic import BaseModel

class FileCreate(BaseModel):
    url: str
    file_type: str
    size: int
    message_id: str

class FileResponse(BaseModel):
    file_id: str
    url: str
    file_type: str
    size: int