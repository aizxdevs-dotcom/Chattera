from fastapi import APIRouter, HTTPException, Depends
from app.crud import invitation as crud
from app.schemas.invitation import InvitationCreate, InvitationResponse
from app.routers.user import get_current_user   # ✅ reuse JWT dependency

router = APIRouter(prefix="/invitations", tags=["Invitations"])

# -------------------------------------------------------------------------
# 🔐 Create an invitation (authenticated)
# -------------------------------------------------------------------------
@router.post("/", response_model=InvitationResponse)
def create_invite(
    data: InvitationCreate,
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    Send a connection invitation. The sender must be the authenticated user.
    """
    # ✅ Ignore/verify sender_uid in payload; always use the token’s user_id
    if data.sender_uid and data.sender_uid != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot send invitation as another user")

    rel = crud.send_invitation(current_user_id, data.receiver_uid)
    if not rel:
        raise HTTPException(status_code=404, detail="Receiver not found")

    return InvitationResponse(
        sender_uid=current_user_id,
        receiver_uid=data.receiver_uid,
        status=rel.status
    )

# -------------------------------------------------------------------------
# 🔐 Respond to an invitation (authenticated)
# -------------------------------------------------------------------------
@router.post("/{sender_uid}/{receiver_uid}/respond", response_model=InvitationResponse)
def respond(
    sender_uid: str,
    receiver_uid: str,
    accept: bool,
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    Accept or decline an invitation. The receiver must be the authenticated user.
    """
    if receiver_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only respond to invitations sent to your own account",
        )

    rel = crud.respond_invitation(sender_uid, receiver_uid, accept)
    if not rel:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return InvitationResponse(
        sender_uid=sender_uid,
        receiver_uid=receiver_uid,
        status=rel.status
    )

# -------------------------------------------------------------------------
# 🔐 List invitations (authenticated)
# -------------------------------------------------------------------------
@router.get("/{user_uid}", response_model=list[InvitationResponse])
def list_invites(
    user_uid: str,
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    List invitations for the given user. Users may only view their own invitations.
    """
    if user_uid != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own invitations"
        )

    invites = crud.list_invitations(user_uid)
    if invites is None:
        raise HTTPException(status_code=404, detail="No invitations found")

    return invites