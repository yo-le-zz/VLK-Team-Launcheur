"""VLK Launcher — FastAPI Server v1.0.1"""
import os
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.server.core.database import init_db
from src.server.core.config import settings
from src.server.routers import auth, licenses, admin, announcements
from src.server.core.ws_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="VLK Launcher API", version="1.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(licenses.router, prefix="/licenses", tags=["licenses"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(announcements.router, prefix="/announcements", tags=["announcements"])

security = HTTPBearer()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "VLK Launcher API", "version": "1.0.1"}

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    from src.server.core.auth_utils import decode_token
    from src.server.core.database import AsyncSessionLocal, User
    from sqlalchemy import select

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role", "user")

    # The JWT only carries sub/username/role — fetch the current avatar_url
    # from the DB so the SAME profile picture is used for both voice chat
    # and text chat, sourced from the single Profil-managed value.
    avatar_url = ""
    try:
        async with AsyncSessionLocal() as session:
            r = await session.execute(select(User).where(User.id == int(user_id)))
            u = r.scalar_one_or_none()
            if u:
                avatar_url = u.avatar_url or ""
    except Exception:
        avatar_url = ""

    await manager.connect(websocket, user_id, username, role, avatar_url)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await manager.handle_message(msg, user_id, username, role)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
