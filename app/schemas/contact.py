from pydantic import BaseModel

class ContactResponse(BaseModel):
    user_uid: str
    contact_uid: str