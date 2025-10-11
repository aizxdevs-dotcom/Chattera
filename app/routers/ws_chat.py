from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import manager
from app.crud.message import message_crud
from app.crud.conversation import conversation_crud
from app.models.user import User
from app.schemas.message import MessageResponse, FileResponse
import logging

# ✅ log router initialization once at import
log = logging.getLogger("uvicorn.error")
log.info("✅ WS router initialized")

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])


@router.websocket("/conversations/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for a conversation.
    Expects client to send JSON:
      {"sender_id": "...", "content": "...", "file_ids": [...]}
    Broadcasts messages to every connected client.
    """
    await manager.connect(conversation_id, websocket)

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception:
                # Client likely disconnected or sent invalid JSON
                log.warning("[WS] Invalid payload or forced close.")
                break

            sender_id = data.get("sender_id")
            content = data.get("content", "")
            file_ids = data.get("file_ids", [])

            # --- Validate conversation ---
            convo = conversation_crud.get_conversation(conversation_id)
            if not convo:
                await websocket.send_json({"error": "Conversation not found."})
                continue

            # --- Validate sender ---
            sender = User.nodes.get_or_none(user_id=sender_id)
            if not sender:
                await websocket.send_json({"error": "Invalid sender_id."})
                continue

            # --- Verify membership ---
            member_ids = [m.user_id for m in convo.members]
            if sender_id not in member_ids:
                await websocket.send_json({"error": "Sender not in this conversation."})
                continue

            # --- Create message in DB ---
            new_message = message_crud.send_message(
                sender_id=sender_id,
                conversation_id=conversation_id,
                content=content,
                file_ids=file_ids,
            )
            if not new_message:
                await websocket.send_json({"error": "Failed to create message."})
                continue

            # --- Build response payload ---
            sender_obj = new_message.sender.single()
            attachments = list(new_message.attachments)

            msg_response = MessageResponse(
                message_id=new_message.message_id,
                content=new_message.content,
                timestamp=new_message.timestamp,
                sender_id=sender_obj.user_id,
                username=getattr(sender_obj, "username", None),
                user_profile_url=getattr(sender_obj, "profile_photo", None),
                conversation_id=conversation_id,
                files=[
                    FileResponse(
                        file_id=f.file_id,
                        url=f.url,
                        file_type=f.file_type,
                        size=f.size,
                    )
                    for f in attachments
                ],
            ).model_dump()

            # --- Broadcast message ---
            await manager.broadcast(conversation_id, msg_response)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
        log.info(f"[WS] Client disconnected from conversation {conversation_id}")
    except Exception as e:
        # Catch-all for unexpected runtime errors; avoids abrupt close
        log.exception(f"[WS] Unexpected error in conversation {conversation_id}: {e}")
        manager.disconnect(conversation_id, websocket)