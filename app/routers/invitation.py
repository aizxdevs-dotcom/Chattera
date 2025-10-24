from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
from app.crud import invitation as crud
from app.crud import contact as contact_crud
from app.schemas.invitation import (
    InvitationCreate, InvitationResponse, 
    InvitationListResponse, InvitationActionResponse
)
from app.routers.user import get_current_user   # ✅ reuse JWT dependency

router = APIRouter(prefix="/invitations", tags=["Invitations"])

# -------------------------------------------------------------------------
# 🔐 Send a friend request (NEW - PRIMARY ENDPOINT)
# -------------------------------------------------------------------------
@router.post("/send", response_model=dict, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    data: InvitationCreate,
    current_user_id: str = Depends(get_current_user)
):
    """
    Send a friend request to another user.
    """
    # Validate: cannot send to yourself
    if data.receiver_uid == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself"
        )
    
    # Check if already friends
    if contact_crud.is_friend(current_user_id, data.receiver_uid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already friends with this user"
        )
    
    rel = crud.send_invitation(current_user_id, data.receiver_uid, data.message)
    
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found"
        )
    
    if isinstance(rel, dict) and "error" in rel:
        if rel["error"] == "already_friends":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already friends with this user"
            )
        elif rel["error"] == "invitation_exists":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Friend request already exists with status: {rel.get('status')}"
            )
        elif rel["error"] == "reverse_invitation_exists":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This user has already sent you a friend request. Check your pending requests."
            )

    return {
        "message": "Friend request sent successfully",
        "sender_uid": current_user_id,
        "receiver_uid": data.receiver_uid,
        "status": "pending"
    }

# -------------------------------------------------------------------------
# 🔐 Get received friend requests (NEW)
# -------------------------------------------------------------------------
@router.get("/received", response_model=InvitationListResponse)
def get_received_invitations(
    status_filter: Optional[str] = Query("pending", description="Filter by status: pending, accepted, declined"),
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all friend requests received by the authenticated user.
    """
    invitations = crud.list_received_invitations(current_user_id, status_filter)
    
    invitation_responses = [
        InvitationResponse(
            sender_uid=inv["sender_uid"],
            receiver_uid=inv["receiver_uid"],
            sender_username=inv.get("sender_username"),
            sender_profile_photo=inv.get("sender_profile_photo"),
            status=inv["status"],
            message=inv.get("message"),
            created_at=inv.get("created_at")
        )
        for inv in invitations
    ]
    
    return InvitationListResponse(
        invitations=invitation_responses,
        total=len(invitation_responses)
    )

# -------------------------------------------------------------------------
# 🔐 Get sent friend requests (NEW)
# -------------------------------------------------------------------------
@router.get("/sent", response_model=InvitationListResponse)
def get_sent_invitations(
    status_filter: Optional[str] = Query("pending", description="Filter by status: pending, accepted, declined"),
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all friend requests sent by the authenticated user.
    """
    invitations = crud.list_sent_invitations(current_user_id, status_filter)
    
    invitation_responses = [
        InvitationResponse(
            sender_uid=inv["sender_uid"],
            receiver_uid=inv["receiver_uid"],
            receiver_username=inv.get("receiver_username"),
            receiver_profile_photo=inv.get("receiver_profile_photo"),
            status=inv["status"],
            message=inv.get("message"),
            created_at=inv.get("created_at")
        )
        for inv in invitations
    ]
    
    return InvitationListResponse(
        invitations=invitation_responses,
        total=len(invitation_responses)
    )

# -------------------------------------------------------------------------
# 🔐 Accept a friend request (NEW)
# -------------------------------------------------------------------------
@router.post("/{sender_uid}/accept", response_model=InvitationActionResponse)
def accept_friend_request(
    sender_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Accept a friend request from another user.
    """
    rel = crud.respond_invitation(sender_uid, current_user_id, accept=True)
    
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    if isinstance(rel, dict) and "error" in rel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept: {rel.get('error')}"
        )
    
    return InvitationActionResponse(
        message="Friend request accepted",
        sender_uid=sender_uid,
        receiver_uid=current_user_id,
        status="accepted"
    )

# -------------------------------------------------------------------------
# 🔐 Decline a friend request (NEW)
# -------------------------------------------------------------------------
@router.post("/{sender_uid}/decline", response_model=InvitationActionResponse)
def decline_friend_request(
    sender_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Decline a friend request from another user.
    """
    rel = crud.respond_invitation(sender_uid, current_user_id, accept=False)
    
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    if isinstance(rel, dict) and "error" in rel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decline: {rel.get('error')}"
        )
    
    return InvitationActionResponse(
        message="Friend request declined",
        sender_uid=sender_uid,
        receiver_uid=current_user_id,
        status="declined"
    )

# -------------------------------------------------------------------------
# 🔐 Cancel a sent friend request (NEW)
# -------------------------------------------------------------------------
@router.delete("/{receiver_uid}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_friend_request(
    receiver_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Cancel a friend request you sent to another user.
    """
    success = crud.cancel_invitation(current_user_id, receiver_uid)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found or cannot be cancelled"
        )
    
    return None

# =========================================================================
# 📌 Legacy endpoints (backward compatible with your existing code)
# =========================================================================

@router.post("/", response_model=InvitationResponse)
def create_invite(
    data: InvitationCreate,
    current_user_id: str = Depends(get_current_user)
):
    """
    LEGACY: Send a connection invitation. Use /send instead.
    """
    if data.sender_uid and data.sender_uid != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot send invitation as another user")

    rel = crud.send_invitation(current_user_id, data.receiver_uid, data.message)
    if not rel:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if isinstance(rel, dict) and "error" in rel:
        raise HTTPException(status_code=400, detail=str(rel))

    return InvitationResponse(
        sender_uid=current_user_id,
        receiver_uid=data.receiver_uid,
        status=getattr(rel, 'status', 'pending')
    )

@router.post("/{sender_uid}/{receiver_uid}/respond", response_model=InvitationResponse)
def respond(
    sender_uid: str,
    receiver_uid: str,
    accept: bool,
    current_user_id: str = Depends(get_current_user)
):
    """
    LEGACY: Accept or decline an invitation. Use /{sender_uid}/accept or /{sender_uid}/decline instead.
    """
    if receiver_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only respond to invitations sent to your own account",
        )

    rel = crud.respond_invitation(sender_uid, receiver_uid, accept)
    if not rel:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if isinstance(rel, dict) and "error" in rel:
        raise HTTPException(status_code=400, detail=str(rel))

    return InvitationResponse(
        sender_uid=sender_uid,
        receiver_uid=receiver_uid,
        status=getattr(rel, 'status', 'accepted' if accept else 'declined')
    )

@router.get("/{user_uid}", response_model=list[InvitationResponse])
def list_invites(
    user_uid: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    LEGACY: List pending invitations. Use /received instead.
    """
    if user_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own invitations"
        )

    invites = crud.list_received_invitations(user_uid, "pending")
    if not invites:
        return []

    return [
        InvitationResponse(
            sender_uid=inv["sender_uid"],
            receiver_uid=inv["receiver_uid"],
            sender_username=inv.get("sender_username"),
            status=inv["status"]
        )
        for inv in invites
    ]