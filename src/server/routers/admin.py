"""VLK Launcher — Admin Router (master-password protected)"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from src.server.core.database import get_db, User, License, Announcement
from src.server.core.config import settings
from src.server.core.ws_manager import manager

router = APIRouter()


# ── Auth guard ────────────────────────────────────────────────────────────────

def check_master(x_master_password: str = Header(None)):
    if x_master_password != settings.MASTER_PASSWORD:
        raise HTTPException(403, "Invalid master password")


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_licenses = (
        await db.execute(select(func.count(License.id)).where(License.active == True))
    ).scalar()
    used_licenses = (
        await db.execute(select(func.count(License.id)).where(License.used_by != ""))
    ).scalar()
    online_now = len(manager.connections)
    return {
        "total_users": total_users,
        "active_licenses": active_licenses,
        "used_licenses": used_licenses,
        "online_now": online_now,
    }


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    r = await db.execute(select(User))
    users = r.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "active": u.active,
            "rank": u.rank,
            "rank_points": u.rank_points,
            "roblox_username": u.roblox_username,
            "license_key": u.license_key,
            "created_at": str(u.created_at),
        }
        for u in users
    ]


class UserPatch(BaseModel):
    active: Optional[bool] = None
    role: Optional[str] = None
    rank: Optional[str] = None
    rank_points: Optional[int] = None


@router.patch("/users/{user_id}")
async def patch_user(
    user_id: int,
    req: UserPatch,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if req.active is not None:
        user.active = req.active
    if req.role is not None:
        user.role = req.role
    if req.rank is not None:
        user.rank = req.rank
    if req.rank_points is not None:
        user.rank_points = req.rank_points
    await db.commit()
    await manager.broadcast(
        {
            "type": "rank_update",
            "user_id": str(user_id),
            "role": user.role,
            "rank": user.rank,
            "rank_points": user.rank_points,
        }
    )
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    await db.delete(user)
    await db.commit()
    return {"ok": True}


# ── Licenses ──────────────────────────────────────────────────────────────────

@router.get("/licenses")
async def list_licenses(db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    r = await db.execute(select(License))
    return [
        {
            "key": l.key,
            "role": l.role,
            "active": l.active,
            "used_by": l.used_by,
            "created_at": str(l.created_at),
        }
        for l in r.scalars().all()
    ]


class LicenseCreate(BaseModel):
    role: str = "user"
    count: int = 1


@router.post("/licenses/generate")
async def generate_licenses(
    req: LicenseCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    keys = []
    for _ in range(min(req.count, 50)):
        key = "VLK-" + secrets.token_hex(6).upper()
        db.add(License(key=key, role=req.role))
        keys.append(key)
    await db.commit()
    return {"generated": keys}


class LicensePatch(BaseModel):
    active: Optional[bool] = None
    role: Optional[str] = None


@router.patch("/licenses/{key}")
async def patch_license(
    key: str,
    req: LicensePatch,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    r = await db.execute(select(License).where(License.key == key))
    lic = r.scalar_one_or_none()
    if not lic:
        raise HTTPException(404, "License not found")
    if req.active is not None:
        lic.active = req.active
    if req.role is not None:
        lic.role = req.role
    await db.commit()
    return {"ok": True}


@router.delete("/licenses/{key}")
async def delete_license(
    key: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    r = await db.execute(select(License).where(License.key == key))
    lic = r.scalar_one_or_none()
    if not lic:
        raise HTTPException(404, "License not found")
    await db.delete(lic)
    await db.commit()
    return {"ok": True}


# ── Announcements ─────────────────────────────────────────────────────────────

class AnnouncementCreate(BaseModel):
    title: str
    body: str
    priority: str = "normal"


@router.get("/announcements")
async def list_announcements(
    db: AsyncSession = Depends(get_db), _=Depends(check_master)
):
    r = await db.execute(
        select(Announcement).order_by(Announcement.created_at.desc())
    )
    return [_ann(a) for a in r.scalars().all()]


@router.post("/announcements")
async def create_announcement(
    req: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    ann = Announcement(title=req.title, body=req.body, priority=req.priority)
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    await manager.broadcast({"type": "announcement", "data": _ann(ann)})
    return _ann(ann)


@router.delete("/announcements/{ann_id}")
async def delete_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_master),
):
    r = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = r.scalar_one_or_none()
    if not ann:
        raise HTTPException(404, "Announcement not found")
    ann.active = False
    await db.commit()
    return {"ok": True}


# ── Broadcast ─────────────────────────────────────────────────────────────────

class BroadcastMsg(BaseModel):
    type: str = "system"
    content: str


@router.post("/broadcast")
async def broadcast(req: BroadcastMsg, _=Depends(check_master)):
    await manager.broadcast({"type": req.type, "content": req.content})
    return {"ok": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ann(a: Announcement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "body": a.body,
        "priority": a.priority,
        "active": a.active,
        "created_at": str(a.created_at),
    }
