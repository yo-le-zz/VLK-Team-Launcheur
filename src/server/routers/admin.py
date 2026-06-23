from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from src.server.core.database import get_db, User, License, Announcement
from src.server.core.config import settings
from src.server.core.auth_utils import require_role
from src.server.core.ws_manager import manager

router = APIRouter()

def check_master(x_master_password: str = Header(None)):
    if x_master_password != settings.MASTER_PASSWORD:
        raise HTTPException(403, "Invalid master password")

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_licenses = (await db.execute(select(func.count(License.id)).where(License.active == True))).scalar()
    used_licenses = (await db.execute(select(func.count(License.id)).where(License.used_by != ""))).scalar()
    online_now = len(manager.connections)
    return {
        "total_users": total_users,
        "active_licenses": active_licenses,
        "used_licenses": used_licenses,
        "online_now": online_now,
    }

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    r = await db.execute(select(User))
    users = r.scalars().all()
    return [{"id": u.id, "username": u.username, "role": u.role, "active": u.active, "rank": u.rank, "roblox_username": u.roblox_username} for u in users]

class UserPatch(BaseModel):
    active: bool = None
    role: str = None
    rank: str = None
    rank_points: int = None

@router.patch("/users/{user_id}")
async def patch_user(user_id: int, req: UserPatch, db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404)
    if req.active is not None:
        user.active = req.active
    if req.role is not None:
        user.role = req.role
    if req.rank is not None:
        user.rank = req.rank
    if req.rank_points is not None:
        user.rank_points = req.rank_points
    await db.commit()
    # broadcast role update
    await manager.broadcast({"type": "role_update", "user_id": str(user_id), "role": user.role, "rank": user.rank})
    return {"ok": True}
