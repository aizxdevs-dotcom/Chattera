from fastapi import (
    APIRouter, HTTPException, status, UploadFile, File, Form, Depends
)
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from typing import Optional, List

from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.file import FileResponse
from app.crud.message import message_crud
from app.crud.file import file_crud
from app.crud.conversation import conversation_crud
from app.routers.user import get_current_user
from app.services.presence_manager import get_active_user_ids
from app.models.user import User

load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")

router = APIRouter(tags=["Messages"])

# ---------------------------------------------------------------------
# 📨  Send new message
# ---------------------------------------------------------------------
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_new_message(
    conversation_id: str = Form(...),
    content: Optional[str] = Form(None),
    upload: Optional[UploadFile] = File(None),
    current_user_id: str = Depends(get_current_user),
):
    """
    Send a message that may include:
      • text only
      • actual file only
      • or both.
    When a file is given, it's uploaded to S3 and stored in Neo4j via file_crud.
    """
    if not content and not upload:
        raise HTTPException(status_code=400, detail="Message must include text or an uploaded file.")

    file_ids: List[str] = []

    # ✅ Handle S3 upload if file exists
    if upload:
        file_ext = os.path.splitext(upload.filename)[1]
        s3_key = f"messages/{uuid4()}{file_ext}"

        s3.upload_fileobj(upload.file, bucket, s3_key)
        file_url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"

        # store File node
        new_file = file_crud.create_file(
            file_url=file_url,
            file_type=upload.content_type,
            size=upload.size if hasattr(upload, "size") else None,
        )
        file_ids = [new_file.file_id]

    # ✅ Create message node
    created = message_crud.send_message(
        sender_id=current_user_id,
        conversation_id=conversation_id,
        content=content,
        file_ids=file_ids,
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
        ) for f in created.attachments
    ]

    return MessageResponse(
        message_id=created.message_id,
        content=created.content,
        timestamp=created.timestamp,
        sender_id=current_user_id,
        username=getattr(sender, "username", None),
        user_profile_url=getattr(sender, "profile_photo", None),
        conversation_id=conversation_id,
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
    content: Optional[str] = Form(None),
    upload: Optional[UploadFile] = File(None),
    current_user_id: str = Depends(get_current_user),
):
    """
    Update message text and/or replace the uploaded file.
    Existing attachments will be replaced if a new file is uploaded.
    """
    message_node = message_crud.get_message_by_id(message_id)
    if not message_node:
        raise HTTPException(status_code=404, detail="Message not found")

    sender_rel = message_node.sender.single()
    if not sender_rel or sender_rel.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own messages.")

    new_file_ids: List[str] = []

    # ✅ Upload new file to S3 if provided
    if upload:
        file_ext = os.path.splitext(upload.filename)[1]
        s3_key = f"messages/{uuid4()}{file_ext}"

        s3.upload_fileobj(upload.file, bucket, s3_key)
        file_url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"

        new_file = file_crud.create_file(
            file_url=file_url,
            file_type=upload.content_type,
            size=upload.size if hasattr(upload, "size") else None,
        )
        new_file_ids = [new_file.file_id]

    # ✅ Update in DB (both content and file)
    updated = message_crud.update_message(
        message_id=message_id, new_content=content, new_file_ids=new_file_ids or None
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update message")

    convo = updated.in_conversation.single()
    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size,
        ) for f in updated.attachments
    ]

    return MessageResponse(
        message_id=updated.message_id,
        content=updated.content,
        timestamp=updated.timestamp,
        sender_id=sender_rel.user_id,
        username=sender_rel.username,
        user_profile_url=sender_rel.profile_photo,
        conversation_id=convo.conversation_id if convo else None,
        files=files,
    )
# ---------------------------------------------------------------------
# ❌  Delete message
# ---------------------------------------------------------------------
@router.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    delete_content: bool = True,
    delete_files: bool = True,
    current_user_id: str = Depends(get_current_user),
):
    """
    Delete a message selectively:
      - ?delete_content=true&delete_files=false → remove only text
      - ?delete_content=false&delete_files=true → remove only attachments
      - both true (default) → delete entire message.
    Only sender may perform this action.
    """
    msg = message_crud.get_message_by_id(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    sender_rel = msg.sender.single()
    if not sender_rel or sender_rel.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own messages.")

    result = message_crud.delete_message(
        message_id,
        delete_content=delete_content,
        delete_files=delete_files,
    )

    # Full deletion returns None
    if result is None:
        return {"detail": "Message fully deleted"}
    feedback = []
    if delete_content:
        feedback.append("content removed")
    if delete_files:
        feedback.append("file(s) removed")
    return {"detail": f"Message updated: {', '.join(feedback)}"}