from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import manager
from app.crud.message import message_crud
from app.crud.conversation import conversation_crud
from app.models.user import User
from app.schemas.message import MessageResponse, FileResponse

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])


@router.websocket("/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for a conversation. Expects the client to send `{"sender_id": ..., "content": ...}` etc.
    Broadcasts all sent messages to every client in the conversation.
    """
    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            sender_id = data.get("sender_id")
            content = data.get("content", "")
            file_ids = data.get("file_ids", [])

            # (Optional) verify sender belongs to conversation
            convo = conversation_crud.get_conversation(conversation_id)
            member_ids = [m.user_id for m in convo.members]
            if sender_id not in member_ids:
                await websocket.send_json({"error": "Not a member of this conversation"})
                continue

            # Save message in DB
            created = message_crud.send_message(sender_id, conversation_id, content, file_ids)
            sender = User.nodes.get(user_id=sender_id)
            files = [
                FileResponse(
                    file_id=f.file_id,
                    url=f.url,
                    file_type=f.file_type,
                    size=f.size,
                ) for f in created.attachments
            ]
            msg = MessageResponse(
                message_id=created.message_id,
                content=created.content,
                timestamp=created.timestamp,
                sender_id=sender.user_id,
                username=sender.username,
                user_profile_url=sender.profile_photo,
                conversation_id=conversation_id,
                files=files,
            ).model_dump()

            # Broadcast message to everyone in room
            await manager.broadcast(conversation_id, msg)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)