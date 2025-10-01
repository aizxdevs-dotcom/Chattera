from pydantic import BaseModel
from typing import Literal

class InvitationCreate(BaseModel):
    sender_uid: str
    receiver_uid: str

class InvitationResponse(BaseModel):
    sender_uid: str
    receiver_uid: str
    status: Literal["pending", "accepted", "declined"]