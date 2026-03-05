"""WebSocket Connection Manager"""
from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    """Manages WebSocket connections for real-time messaging"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a user's websocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"✅ User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        """Disconnect a user's websocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            print(f"❌ User {user_id} disconnected")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
    
    async def broadcast(self, message: dict, exclude_user: str = None):
        """Broadcast message to all connected users"""
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {user_id}: {e}")
