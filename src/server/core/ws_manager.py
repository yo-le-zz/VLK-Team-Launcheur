import json
from datetime import datetime, timezone
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, dict] = {}   # user_id -> {ws, username, role}
        self.voice_room: Set[str] = set()        # user_ids currently in voice

    async def connect(self, websocket: WebSocket, user_id: str, username: str, role: str):
        await websocket.accept()
        # Keep avatar_url in memory for WS relays (chat + voice)
        # Avatar_url comes from the HTTP login payload (user.avatar_url) -> token claims are limited,
        # so we also accept it via websocket join payload if client provides it.
        avatar_url = None
        try:
            # If client already sent an avatar_url in username/role fields, it won't exist here.
            avatar_url = getattr(websocket, "avatar_url", None)
        except Exception:
            avatar_url = None

        self.connections[user_id] = {
            "ws": websocket,
            "username": username,
            "role": role,
            "avatar_url": avatar_url or "",
        }
        await self.broadcast({
                "type": "presence", "action": "join",
                "user_id": user_id, "username": username, "role": role,
            })
        await self.send_online_list(websocket)
        # Send current voice room participants
        if self.voice_room:
            users = [
                {
                    "user_id": uid,
                    "username": self.connections[uid]["username"],
                    "avatar_url": self.connections[uid].get("avatar_url", ""),
                }
                for uid in self.voice_room if uid in self.connections
            ]
            await websocket.send_text(json.dumps({"type": "voice_users", "users": users}))

    async def disconnect(self, user_id: str):
        info = self.connections.pop(user_id, None)
        self.voice_room.discard(user_id)
        if info:
            await self.broadcast({
                "type": "presence", "action": "leave",
                "user_id": user_id, "username": info["username"],
            })

    async def send_online_list(self, websocket: WebSocket):
        members = [
            {"user_id": uid, "username": c["username"], "role": c["role"]}
            for uid, c in self.connections.items()
        ]
        await websocket.send_text(json.dumps({"type": "online_list", "members": members}))

    async def broadcast(self, data: dict, exclude: str = None):
        text = json.dumps(data)
        dead = []
        for uid, conn in self.connections.items():
            if uid == exclude:
                continue
            try:
                await conn["ws"].send_text(text)
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.connections.pop(uid, None)
            self.voice_room.discard(uid)

    async def broadcast_voice(self, data: dict, exclude: str):
        """Relay audio only to users currently in voice room."""
        text = json.dumps(data)
        dead = []
        for uid in list(self.voice_room):
            if uid == exclude:
                continue
            conn = self.connections.get(uid)
            if not conn:
                dead.append(uid)
                continue
            try:
                await conn["ws"].send_text(text)
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.voice_room.discard(uid)

    async def handle_message(self, msg: dict, user_id: str, username: str, role: str):
        t = msg.get("type")

        if t == "chat":
            content = str(msg.get("content", ""))[:512]
            # Always include avatar_url so the client can render the same PDP everywhere
            avatar_url = ""
            # If avatar_url is present in the connection info, reuse it
            # (connections[user_id] currently stores: ws, username, role)
            conn_info = self.connections.get(user_id) or {}
            avatar_url = conn_info.get("avatar_url", "") or ""

            await self.broadcast({
                "type": "chat",
                "user_id": user_id, "username": username, "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "avatar_url": avatar_url,
            })

        elif t == "ping":
            conn = self.connections.get(user_id)
            if conn:
                await conn["ws"].send_text(json.dumps({"type": "pong"}))

        elif t == "rank_update" and role in ("admin", "superadmin"):
            await self.broadcast({
                "type": "rank_update",
                "target_user_id": msg.get("target_user_id"),
                "rank": msg.get("rank"), "by": username,
            })

        # ── Voice ──────────────────────────────────────────────────────────────
        elif t == "voice_join":
            self.voice_room.add(user_id)
            await self.broadcast({
                "type": "voice_join", "user_id": user_id, "username": username,
            }, exclude=user_id)

        elif t == "voice_leave":
            self.voice_room.discard(user_id)
            await self.broadcast({
                "type": "voice_leave", "user_id": user_id, "username": username,
            }, exclude=user_id)

        elif t == "voice_audio":
            # Relay encoded audio to everyone in voice room except sender
            await self.broadcast_voice({
                "type": "voice_audio",
                "from": username,
                "user_id": user_id,
                "data": msg.get("data", ""),
            }, exclude=user_id)

manager = ConnectionManager()
