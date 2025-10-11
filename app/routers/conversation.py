from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationMember
from app.crud.conversation import conversation_crud
from app.routers.user import get_current_user
from app.services.presence_manager import is_user_active

router = APIRouter(prefix="/api", tags=["Conversations"])


# ------------------------------------------------------------------
# Create conversation
# ------------------------------------------------------------------
@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    convo_data: ConversationCreate,
    current_user_id: str = Depends(get_current_user),
):
    """
    Create a new conversation with the provided member IDs.
    The current authenticated user is always included.
    """
    member_ids = set(convo_data.member_ids)
    member_ids.add(current_user_id)

    convo = conversation_crud.create_conversation(
        is_group=convo_data.is_group,
        member_ids=list(member_ids),
    )
    if not convo:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    members: List[ConversationMember] = []
    for u in convo.members:
        active = await is_user_active(u.user_id)
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
# List all conversations for current user  ← fix for 405
# ------------------------------------------------------------------
@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    status_code=status.HTTP_200_OK,
)
async def list_user_conversations(current_user_id: str = Depends(get_current_user)):
    """
    Return all conversations that include the authenticated user.
    Adds online/offline status for each member via Redis.
    """
    convos = conversation_crud.list_user_conversations(current_user_id)
    responses: List[ConversationResponse] = []

    for convo in convos:
        members: List[ConversationMember] = []
        for u in convo.members:
            active = await is_user_active(u.user_id)
            members.append(
                ConversationMember(
                    user_id=u.user_id,
                    username=u.username,
                    user_profile_url=u.profile_photo,
                    is_active=active,
                )
            )

        responses.append(
            ConversationResponse(
                conversation_id=convo.conversation_id,
                is_group=convo.is_group,
                members=members,
            )
        )

    return responses


# ------------------------------------------------------------------
# Get single conversation
# ------------------------------------------------------------------
@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Retrieve one conversation; only members may access."""
    convo = conversation_crud.get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    member_nodes = list(convo.members)
    member_ids = [m.user_id for m in member_nodes]
    if current_user_id not in member_ids:
        raise HTTPException(
            status_code=403,
            detail="Access denied: not a member of this conversation",
        )

    members: List[ConversationMember] = []
    for u in member_nodes:
        active = await is_user_active(u.user_id)
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
# Update conversation (e.g., toggle group/private)
# ------------------------------------------------------------------
@router.put(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_conversation(
    conversation_id: str,
    data: ConversationCreate,
    current_user_id: str = Depends(get_current_user),
):
    """Update conversation metadata such as group status."""
    convo = conversation_crud.update_conversation(
        conversation_id, is_group=data.is_group
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    members: List[ConversationMember] = []
    for u in convo.members:
        active = await is_user_active(u.user_id)
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
@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Delete a conversation if it exists."""
    success = conversation_crud.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return  # 204 → empty body


# ------------------------------------------------------------------
# Add / Remove members
# ------------------------------------------------------------------
@router.post(
    "/conversations/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def add_member_to_conversation(
    conversation_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Add a user to an existing conversation (only members can add)."""
    convo = conversation_crud.get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ensure current user is already a member
    member_ids = [m.user_id for m in convo.members]
    if current_user_id not in member_ids:
        raise HTTPException(status_code=403, detail="You are not a member of this conversation")

    convo = conversation_crud.add_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")

    from app.crud.user import user_crud  # inline import to avoid circular reference
    user = user_crud.get_user_by_id(user_id)
    username = getattr(user, "username", user_id)

    return {"detail": f"{username} added to the conversation"}
@router.delete(
    "/conversations/{conversation_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_member_from_conversation(
    conversation_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Remove a user from a conversation (must be an existing member)."""
    convo = conversation_crud.get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ensure current user is a member
    member_ids = [m.user_id for m in convo.members]
    if current_user_id not in member_ids:
        raise HTTPException(status_code=403, detail="You are not a member of this conversation")

    convo = conversation_crud.remove_member(conversation_id, user_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation or User not found")

    from app.crud.user import user_crud
    user = user_crud.get_user_by_id(user_id)
    username = getattr(user, "username", user_id)

    return {"detail": f"{username} removed from the conversation"}