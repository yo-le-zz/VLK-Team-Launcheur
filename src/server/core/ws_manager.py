import json
from datetime import datetime, timezone
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, dict] = {}   # user_id -> {ws, username, role, avatar_url}
        self.voice_room: Set[str] = set()        # user_ids currently in voice

    async def connect(self, websocket: WebSocket, user_id: str, username: str, role: str, avatar_url: str = ""):
        await websocket.accept()
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
            # Always include avatar_url so the client can render the same PDP
            # everywhere (text chat AND voice chat use this single value).
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

        elif t == "avatar_update":
            # Update avatar_url in connection when user changes profile picture
            new_avatar = msg.get("avatar_url", "")
            if user_id in self.connections:
                self.connections[user_id]["avatar_url"] = new_avatar
            # Broadcast to all clients so they update their UI
            await self.broadcast({
                "type": "avatar_update",
                "user_id": user_id,
                "username": username,
                "avatar_url": new_avatar,
            })

        # ── Voice ──────────────────────────────────────────────────────────────
        elif t == "voice_join":
            self.voice_room.add(user_id)
            conn_info = self.connections.get(user_id) or {}
            avatar_url = msg.get("avatar_url") or conn_info.get("avatar_url", "") or ""
            # Keep the connection's avatar_url in sync, in case the client
            # sent a fresher one in the voice_join payload.
            if avatar_url and user_id in self.connections:
                self.connections[user_id]["avatar_url"] = avatar_url
            await self.broadcast({
                "type": "voice_join", "user_id": user_id, "username": username,
                "avatar_url": avatar_url,
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
