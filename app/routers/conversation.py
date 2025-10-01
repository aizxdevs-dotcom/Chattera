from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4

from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.crud.conversation import conversation_crud   # ✅ use the CRUD singleton
from app.routers.user import get_current_user

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
def create_new_conversation(conversation: ConversationCreate, current_user: str = Depends(get_current_user)):
    """Create a new conversation with members."""
    conversation_id = str(uuid4())
    created_conversation = conversation_crud.create_conversation(
        conversation_id,
        is_group=conversation.is_group,
        member_ids=conversation.member_ids  # ✅ FIX: pass member_ids
    )

    if not created_conversation:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    # Optionally auto-add the current user as a member too
    conversation_crud.add_member(conversation_id, current_user)

    return ConversationResponse(
        conversation_id=created_conversation.conversation_id,
        is_group=created_conversation.is_group,
        member_ids=[m.user_id for m in created_conversation.members]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str):
    """Retrieve a conversation by ID."""
    convo = conversation_crud.get_conversation(conversation_id)  # ✅ FIX: use get_conversation
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        conversation_id=convo.conversation_id,
        is_group=convo.is_group,
        member_ids=[m.user_id for m in convo.members]  # ✅ include members
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(conversation_id: str, updated: ConversationCreate):
    """Update conversation properties (currently only is_group)."""
    convo = conversation_crud.update_conversation(conversation_id, is_group=updated.is_group)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        conversation_id=convo.conversation_id,
        is_group=convo.is_group,
        member_ids=[m.user_id for m in convo.members]
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete a conversation by ID."""
    success = conversation_crud.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"detail": "Conversation deleted successfully"}

@router.post("/conversations/{conversation_id}/members/{user_id}")
def add_member(conversation_id: str, user_id: str):
    """Add a member to a conversation."""
    convo = conversation_crud.add_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")
    return {"detail": f"User {user_id} added to conversation {conversation_id}"}


@router.delete("/conversations/{conversation_id}/members/{user_id}")
def remove_member(conversation_id: str, user_id: str):
    """Remove a member from a conversation."""
    convo = conversation_crud.remove_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")
    return {"detail": f"User {user_id} removed from conversation {conversation_id}"}