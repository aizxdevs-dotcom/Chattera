from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from app.crud import contact as crud
from app.crud import invitation as invitation_crud
from app.schemas.contact import (
    ContactResponse, ContactListResponse, 
    ContactStatsResponse, MutualFriendsResponse
)
from app.routers.user import get_current_user   # ✅ reuse existing JWT dependency

router = APIRouter(prefix="/contacts", tags=["Contacts"])


# -------------------------------------------------------------------------
# 🔐 Get all friends (NEW - PRIMARY ENDPOINT)
# -------------------------------------------------------------------------
@router.get("/", response_model=ContactListResponse)
def get_all_friends(
    search: Optional[str] = Query(None, description="Search friends by username or full name"),
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all friends of the authenticated user.
    """
    if search:
        contacts = crud.search_contacts(current_user_id, search)
    else:
        contacts = crud.list_contacts(current_user_id)
    
    contact_responses = [ContactResponse(**contact) for contact in contacts]
    
    return ContactListResponse(
        contacts=contact_responses,
        total=len(contact_responses)
    )

# -------------------------------------------------------------------------
# 🔐 Get friend statistics (NEW)
# -------------------------------------------------------------------------
@router.get("/stats", response_model=ContactStatsResponse)
def get_friend_stats(
    current_user_id: str = Depends(get_current_user)
):
    """
    Get friendship statistics for the authenticated user.
    """
    total_friends = crud.get_contact_count(current_user_id)
    pending_sent = invitation_crud.count_pending_sent(current_user_id)
    pending_received = invitation_crud.count_pending_received(current_user_id)
    
    return ContactStatsResponse(
        total_friends=total_friends,
        pending_sent=pending_sent,
        pending_received=pending_received
    )

# -------------------------------------------------------------------------
# 🔐 Get mutual friends (NEW)
# -------------------------------------------------------------------------
@router.get("/mutual/{other_uid}", response_model=MutualFriendsResponse)
def get_mutual_friends(
    other_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get mutual friends between authenticated user and another user.
    """
    mutual_friends = crud.get_mutual_friends(current_user_id, other_uid)
    
    mutual_responses = [ContactResponse(**friend) for friend in mutual_friends]
    
    return MutualFriendsResponse(
        mutual_friends=mutual_responses,
        count=len(mutual_responses)
    )

# -------------------------------------------------------------------------
# 🔐 Remove a friend (NEW)
# -------------------------------------------------------------------------
@router.delete("/{friend_uid}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Remove a friend (unfriend).
    """
    if not crud.is_friend(current_user_id, friend_uid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not friends with this user"
        )
    
    success = crud.remove_contact(current_user_id, friend_uid)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove friend"
        )
    
    return None

# =========================================================================
# 📌 Legacy endpoint (backward compatible)
# =========================================================================

@router.get("/{user_uid}", response_model=List[ContactResponse])
def get_contacts(
    user_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    LEGACY: Retrieve the contact list for a user. Use / instead.
    """
    if user_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own contacts."
        )

    contacts = crud.list_contacts(user_uid)
    if not contacts:
        return []

    return [ContactResponse(**contact) for contact in contacts]