from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.crud import contact as crud
from app.schemas.contact import ContactResponse
from app.routers.user import get_current_user   # ✅ reuse existing JWT dependency

router = APIRouter(prefix="/contacts", tags=["Contacts"])


# -------------------------------------------------------------------------
# 🔐 Get contacts (authenticated)
# -------------------------------------------------------------------------
@router.get("/{user_uid}", response_model=List[ContactResponse])
def get_contacts(
    user_uid: str,
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    Retrieve the contact list for a user.
    Users may only view their own contacts.
    """
    if user_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own contacts."
        )

    contacts = crud.list_contacts(user_uid)
    if contacts is None:
        raise HTTPException(status_code=404, detail="Contacts not found")

    return contacts