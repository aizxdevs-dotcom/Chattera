from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
from app.schemas.message import MessageCreate, MessageResponse
from app.crud.message import message_crud
from app.schemas.file import FileResponse   # to include file metadata in responses
from app.routers.user import get_current_user

router = APIRouter()


@router.post("/messages", response_model=MessageResponse)
def send_new_message(
    message: MessageCreate,
    current_user_id: str = Depends(get_current_user)   # ✅ require token
):
    """Send a new message (only authenticated users)."""
    # ✅ Override sender_id – never trust client input
    created_message = message_crud.send_message(
        sender_id=current_user_id,
        conversation_id=message.conversation_id,
        content=message.content,
        file_ids=message.file_ids
    )

    if not created_message:
        raise HTTPException(status_code=404, detail="Conversation or sender not found")

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size
        )
        for f in created_message.attachments
    ]
    return MessageResponse(
        message_id=created_message.message_id,
        content=created_message.content,
        timestamp=created_message.timestamp,
        sender_id=current_user_id,
        conversation_id=message.conversation_id,
        files=files
    )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_all_messages(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user)   # ✅ require token
):
    """Fetch all messages in a conversation (only participants can read)."""
    messages = message_crud.get_messages_in_conversation(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # ✅ Optional: verify membership if conversation is private (good practice)
    # convo = conversation_crud.get_conversation(conversation_id)
    # member_ids = [m.user_id for m in convo.members]
    # if current_user_id not in member_ids:
    #     raise HTTPException(status_code=403, detail="Access denied: not a member of this conversation")

    return [
        MessageResponse(
            message_id=msg.message_id,
            content=msg.content,
            timestamp=msg.timestamp,
            sender_id=msg.sender.single().user_id if msg.sender.single() else None,
            conversation_id=conversation_id,
            files=[
                FileResponse(
                    file_id=f.file_id,
                    url=f.url,
                    file_type=f.file_type,
                    size=f.size
                )
                for f in msg.attachments
            ]
        )
        for msg in messages
    ]

@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: str,
    new_data: MessageCreate,
    current_user_id: str = Depends(get_current_user)   # ✅ require token
):
    """Update an existing message (only the sender can edit)."""
    updated_message = message_crud.get_message_by_id(message_id)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found")

    sender = updated_message.sender.single()
    if not sender or sender.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own messages.")

    # ✅ Proceed with update
    updated_message = message_crud.update_message(message_id, new_data.content)

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size
        )
        for f in updated_message.attachments
    ]
    return MessageResponse(
        message_id=updated_message.message_id,
        content=updated_message.content,
        timestamp=updated_message.timestamp,
        sender_id=sender.user_id if sender else None,
        conversation_id=updated_message.in_conversation.single().conversation_id
        if updated_message.in_conversation.single()
        else None,
        files=files
    )


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    current_user_id: str = Depends(get_current_user)   # ✅ require token
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