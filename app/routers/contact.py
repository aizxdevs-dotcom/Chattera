from fastapi import APIRouter
from typing import List

# Always go through app.* so Python resolves the package correctly
from app.crud import contact as crud
from app.schemas.contact import ContactResponse

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("/{user_uid}", response_model=List[ContactResponse])
def get_contacts(user_uid: str):
    return crud.list_contacts(user_uid)