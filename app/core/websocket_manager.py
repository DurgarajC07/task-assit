"""WebSocket connection manager."""
from typing import Dict
from fastapi import WebSocket
import uuid


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: uuid.UUID):
        """Remove a disconnected WebSocket."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: uuid.UUID, message: dict):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception:
                await self.disconnect(user_id)

    async def broadcast_to_user(self, user_id: uuid.UUID, event_type: str,
                               data: dict):
        """Broadcast an event to a specific user."""
        from datetime import datetime

        message = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_personal_message(user_id, message)
