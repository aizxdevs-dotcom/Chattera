from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import asyncio

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationMember,
)
from app.crud.conversation import conversation_crud
from app.routers.user import get_current_user
from app.services.presence_manager import is_user_active

router = APIRouter()


# ------------------------------------------------------------------
# Create conversation
# ------------------------------------------------------------------
@router.post("/conversations",
             response_model=ConversationResponse,
             status_code=status.HTTP_201_CREATED)
def create_conversation(
    convo_data: ConversationCreate,
    current_user_id: str = Depends(get_current_user),
):
    """
    Create a new conversation with provided member IDs.
    Automatically adds the current user if not in the list.
    """
    member_ids = set(convo_data.member_ids)
    member_ids.add(current_user_id)  # include creator

    convo = conversation_crud.create_conversation(
        is_group=convo_data.is_group,
        member_ids=list(member_ids),
    )
    if not convo:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    members: list[ConversationMember] = []
    for u in convo.members:
        active = asyncio.run(is_user_active(u.user_id))  # 🔹 check presence
        members.append(
            ConversationMember(
                user_id=u.user_id,
                username=u.username,
                user_profile_url=u.profile_photo,
                is_active=active,
            )
        )

    return ConversationResponse(
        conversation_id=convo.conversation_id,
        is_group=convo.is_group,
        members=members,
    )


# ------------------------------------------------------------------
# Get single conversation
# ------------------------------------------------------------------
@router.get("/conversations/{conversation_id}",
            response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Retrieve a conversation by ID, only for members."""
    convo = conversation_crud.get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    member_nodes = list(convo.members)
    member_ids = [m.user_id for m in member_nodes]
    if current_user_id not in member_ids:
        raise HTTPException(
            status_code=403,
            detail="Access denied: not a member of this conversation"
        )

    members: list[ConversationMember] = []
    for u in member_nodes:
        active = asyncio.run(is_user_active(u.user_id))  # 🔹 include activity flag
        members.append(
            ConversationMember(
                user_id=u.user_id,
                username=u.username,
                user_profile_url=u.profile_photo,
                is_active=active,
            )
        )

    return ConversationResponse(
        conversation_id=convo.conversation_id,
        is_group=convo.is_group,
        members=members,
    )


# ------------------------------------------------------------------
# Update conversation (e.g. group/private toggle)
# ------------------------------------------------------------------
@router.put("/conversations/{conversation_id}",
            response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    data: ConversationCreate,
    current_user_id: str = Depends(get_current_user),
):
    convo = conversation_crud.update_conversation(
        conversation_id, is_group=data.is_group
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    members: list[ConversationMember] = []
    for u in convo.members:
        active = asyncio.run(is_user_active(u.user_id))
        members.append(
            ConversationMember(
                user_id=u.user_id,
                username=u.username,
                user_profile_url=u.profile_photo,
                is_active=active,
            )
        )

    return ConversationResponse(
        conversation_id=convo.conversation_id,
        is_group=convo.is_group,
        members=members,
    )


# ------------------------------------------------------------------
# Delete conversation
# ------------------------------------------------------------------
@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
):
    success = conversation_crud.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"detail": "Conversation deleted successfully"}


# ------------------------------------------------------------------
# Add/Remove members
# ------------------------------------------------------------------
@router.post("/conversations/{conversation_id}/members/{user_id}")
def add_member_to_conversation(
    conversation_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user),
):
    convo = conversation_crud.add_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")
    return {"detail": f"User {user_id} added to conversation {conversation_id}"}


@router.delete("/conversations/{conversation_id}/members/{user_id}")
def remove_member_from_conversation(
    conversation_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user),
):
    convo = conversation_crud.remove_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")
    return {"detail": f"User {user_id} removed from conversation {conversation_id}"}