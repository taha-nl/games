import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # team_id -> list of WebSocket (for targeted messages)
        self.team_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, team_id: int | None = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if team_id:
            self.team_connections.setdefault(team_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, team_id: int | None = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if team_id and team_id in self.team_connections:
            conns = self.team_connections[team_id]
            if websocket in conns:
                conns.remove(websocket)

    async def broadcast(self, data: dict[str, Any]):
        message = json.dumps(data)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to_team(self, team_id: int, data: dict[str, Any]):
        message = json.dumps(data)
        conns = self.team_connections.get(team_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, team_id)


manager = ConnectionManager()
