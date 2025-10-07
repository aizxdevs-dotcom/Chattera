from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

# Store all active connections
active_connections: List[WebSocket] = []

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Receive message from one client
            data = await websocket.receive_text()
            
            # Broadcast message to all connected clients
            for conn in active_connections:
                await conn.send_text(data)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
