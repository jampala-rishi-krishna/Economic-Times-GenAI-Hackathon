"""
WebSocket Connection Manager for NEXUS
"""
import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket
import uuid
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # meeting_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # global connections (no meeting filter)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, meeting_id: str = None):
        await websocket.accept()
        if meeting_id:
            if meeting_id not in self.active_connections:
                self.active_connections[meeting_id] = set()
            self.active_connections[meeting_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, meeting_id: str = None):
        if meeting_id and meeting_id in self.active_connections:
            self.active_connections[meeting_id].discard(websocket)
        else:
            self.global_connections.discard(websocket)

    async def send_to_meeting(self, meeting_id: str, message: dict):
        """Broadcast message to all clients watching a specific meeting."""
        message_str = json.dumps(message, default=str)
        dead = set()

        # Send to meeting-specific connections
        if meeting_id in self.active_connections:
            for ws in self.active_connections[meeting_id]:
                try:
                    await ws.send_text(message_str)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.active_connections[meeting_id].discard(ws)

        # Also broadcast to global listeners
        dead_global = set()
        for ws in self.global_connections:
            try:
                await ws.send_text(message_str)
            except Exception:
                dead_global.add(ws)
        for ws in dead_global:
            self.global_connections.discard(ws)

    async def broadcast_all(self, message: dict):
        """Broadcast to ALL connections."""
        message_str = json.dumps(message, default=str)
        all_sockets = list(self.global_connections)
        for conns in self.active_connections.values():
            all_sockets.extend(conns)
        dead = []
        for ws in all_sockets:
            try:
                await ws.send_text(message_str)
            except Exception:
                dead.append(ws)

    def build_event(self, meeting_id: str, event_type: str, agent_name: str,
                    agent_role: str, message: str, data: dict = None) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "meeting_id": meeting_id,
            "event_type": event_type,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "message": message,
            "data": data or {}
        }


# Singleton instance
manager = ConnectionManager()
