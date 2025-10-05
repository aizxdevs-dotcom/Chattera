from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import asyncio

from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.file import FileResponse
from app.schemas.conversation import ConversationMember
from app.crud.message import message_crud
from app.crud.conversation import conversation_crud
from app.routers.user import get_current_user
from app.services.presence_manager import get_active_user_ids
from app.models.user import User  # needed for active user lookup

router = APIRouter(tags=["Messages"])


# ---------------------------------------------------------------------
# 📨  Send new message
# ---------------------------------------------------------------------
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_new_message(
    message: MessageCreate,
    current_user_id: str = Depends(get_current_user),
):
    """Send a new message (text, file, or both)."""
    created = message_crud.send_message(
        sender_id=current_user_id,
        conversation_id=message.conversation_id,
        content=message.content,
        file_ids=message.file_ids,
    )
    if not created:
        raise HTTPException(status_code=404, detail="Conversation or sender not found")

    sender = created.sender.single()
    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size,
        )
        for f in created.attachments
    ]

    return MessageResponse(
        message_id=created.message_id,
        content=created.content,
        timestamp=created.timestamp,
        sender_id=current_user_id,
        username=getattr(sender, "username", None),
        user_profile_url=getattr(sender, "profile_photo", None),
        conversation_id=message.conversation_id,
        files=files,
    )


# ---------------------------------------------------------------------
# 💬  Get all messages in a conversation
# ---------------------------------------------------------------------
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_all_messages(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Fetch all messages in a conversation (only participants can read)."""
    messages = message_crud.get_messages_in_conversation(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Optional: verify membership (good practice)
    convo = conversation_crud.get_conversation(conversation_id)
    member_ids = [m.user_id for m in convo.members]
    if current_user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Access denied: not a member of this conversation")

    results: list[MessageResponse] = []
    for msg in messages:
        sender = msg.sender.single()
        results.append(
            MessageResponse(
                message_id=msg.message_id,
                content=msg.content,
                timestamp=msg.timestamp,
                sender_id=getattr(sender, "user_id", None),
                username=getattr(sender, "username", None),
                user_profile_url=getattr(sender, "profile_photo", None),
                conversation_id=conversation_id,
                files=[
                    FileResponse(
                        file_id=f.file_id,
                        url=f.url,
                        file_type=f.file_type,
                        size=f.size,
                    )
                    for f in msg.attachments
                ],
            )
        )

    return results


# ---------------------------------------------------------------------
# ✏️  Update existing message
# ---------------------------------------------------------------------
@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: str,
    new_data: MessageCreate,
    current_user_id: str = Depends(get_current_user),
):
    """Update an existing message (only the sender can edit)."""
    message_node = message_crud.get_message_by_id(message_id)
    if not message_node:
        raise HTTPException(status_code=404, detail="Message not found")

    sender = message_node.sender.single()
    if not sender or sender.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own messages.")

    updated_message = message_crud.update_message(message_id, new_data.content)
    if not updated_message:
        raise HTTPException(status_code=500, detail="Failed to update message")

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size,
        )
        for f in updated_message.attachments
    ]

    convo = updated_message.in_conversation.single()
    return MessageResponse(
        message_id=updated_message.message_id,
        content=updated_message.content,
        timestamp=updated_message.timestamp,
        sender_id=sender.user_id,
        username=sender.username,
        user_profile_url=sender.profile_photo,
        conversation_id=convo.conversation_id if convo else None,
        files=files,
    )


# ---------------------------------------------------------------------
# ❌  Delete message
# ---------------------------------------------------------------------
@router.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    current_user_id: str = Depends(get_current_user),
):
    """Delete a message (only the sender can delete)."""
    message = message_crud.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    sender = message.sender.single()
    if not sender or sender.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own messages.")

    success = message_crud.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete message")

    return {"detail": "Message deleted successfully"}


# ---------------------------------------------------------------------
# 🟢  Get currently active users (from Redis presence)
# ---------------------------------------------------------------------
@router.get("/active-users", response_model=List[ConversationMember])
def list_active_users():
    """Return all users currently marked active in Redis."""
    ids = asyncio.run(get_active_user_ids())
    active_users: list[ConversationMember] = []

    for uid in ids:
        u = User.nodes.get_or_none(user_id=uid)
        if u:
            active_users.append(
                ConversationMember(
                    user_id=u.user_id,
                    username=u.username,
                    user_profile_url=u.profile_photo,
                    is_active=True,
                )
            )

    return active_users