from typing import Dict, List
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    """
    Tracks active websocket connections by conversation_id.
    {"<conversation_id>": [list of sockets]}
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        print(f"[WS] Connected → conversation {conversation_id}, total: {len(self.active_connections[conversation_id])}")

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
            print(f"[WS] Disconnected → conversation {conversation_id}")

    async def broadcast(self, conversation_id: str, message: dict):
        """
        Send JSON message to all clients in a conversation.
        Safely skip broken connections.
        """
        connections = self.active_connections.get(conversation_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(conversation_id, ws)


# Singleton instance
manager = ConnectionManager()