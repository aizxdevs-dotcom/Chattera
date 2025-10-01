from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime

from app.schemas.message import MessageCreate, MessageResponse
from app.crud.message import message_crud

router = APIRouter()


@router.post("/messages", response_model=MessageResponse)
def send_new_message(message: MessageCreate):
    """Create and send a new message."""
    message_id = str(uuid4())
    timestamp = datetime.utcnow()  # keep datetime

    created_message = message_crud.send_message(
        message_id=message_id,
        content=message.content,
        timestamp=timestamp,
        sender_id=message.sender_id,
        conversation_id=message.conversation_id,
    )
    if not created_message:
        raise HTTPException(status_code=500, detail="Failed to send message")

    # MessageResponse will auto-serialize datetime into ISO
    return MessageResponse(
        message_id=created_message.message_id,
        content=created_message.content,
        timestamp=created_message.timestamp,
        sender_id=message.sender_id,
        conversation_id=message.conversation_id,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_all_messages(conversation_id: str):
    """Fetch all messages in a given conversation."""
    messages = message_crud.get_messages_in_conversation(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # return [] if no messages for REST best-practice
    return [
        MessageResponse(
            message_id=msg.message_id,
            content=msg.content,
            timestamp=msg.timestamp,
            sender_id=msg.sender.single().user_id if msg.sender.single() else None,
            conversation_id=conversation_id,
        )
        for msg in messages
    ]


@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message(message_id: str, new_data: MessageCreate):
    """Update the content of an existing message."""
    updated_message = message_crud.update_message(message_id, new_data.content)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found")

    sender = updated_message.sender.single()
    return MessageResponse(
        message_id=updated_message.message_id,
        content=updated_message.content,
        timestamp=updated_message.timestamp,
        sender_id=sender.user_id if sender else None,
        conversation_id=updated_message.in_conversation.single().conversation_id
        if updated_message.in_conversation.single()
        else None,
    )


@router.delete("/messages/{message_id}")
def delete_message(message_id: str):
    """Delete a message by ID."""
    success = message_crud.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"detail": "Message deleted successfully"}