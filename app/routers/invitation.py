from fastapi import APIRouter, HTTPException
from app.crud import invitation as crud
from app.schemas.invitation import InvitationCreate, InvitationResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/invitations", tags=["Invitations"])

@router.post("/", response_model=InvitationResponse)
def create_invite(data: InvitationCreate):
    rel = crud.send_invitation(data.sender_uid, data.receiver_uid)
    return {"sender_uid": data.sender_uid, "receiver_uid": data.receiver_uid, "status": rel.status}

@router.post("/{sender_uid}/{receiver_uid}/respond", response_model=InvitationResponse)
def respond(sender_uid: str, receiver_uid: str, accept: bool):
    rel = crud.respond_invitation(sender_uid, receiver_uid, accept)
    if not rel:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return {"sender_uid": sender_uid, "receiver_uid": receiver_uid, "status": rel.status}

@router.get("/{user_uid}", response_model=list[InvitationResponse])
def list_invites(user_uid: str):
    return crud.list_invitations(user_uid)