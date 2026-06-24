"""VLK Launcher — Admin Router
Auth: JWT token required for admin operations (admin or superadmin role)
Master password can be used to get a temporary admin token for initial setup.
"""
import secrets
import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from src.server.core.database import get_db, User, License, Announcement
from src.server.core.config import settings
from src.server.core.ws_manager import manager
from src.server.core.auth_utils import decode_token, create_token, require_role

router = APIRouter()


# ── Auth dependencies ─────────────────────────────────────────────────────────

def check_master(
    password: str = Query(None),
    x_master_password: str = Header(None)
):
    # Accept password from query parameter or header
    auth_password = password or x_master_password
    if not auth_password or auth_password != settings.MASTER_PASSWORD:
        raise HTTPException(403, "Invalid master password")


def get_current_admin(payload: dict = Depends(require_role("admin", "superadmin"))):
    """Vérifie que l'utilisateur a un rôle admin ou superadmin"""
    return payload


def get_current_superadmin(payload: dict = Depends(require_role("superadmin"))):
    """Vérifie que l'utilisateur a un rôle superadmin"""
    return payload


# ── Serve Admin Panel HTML ───────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def admin_panel():
    """Serve the admin panel HTML interface."""
    # Get the absolute path to the static directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, "..", "static")
    admin_html_path = os.path.join(static_dir, "admin.html")
    
    if os.path.exists(admin_html_path):
        with open(admin_html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(404, "Admin panel not found")


# ── Admin Login (Master Password) ────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    username: str
    password: str
    master_password: str

@router.post("/login")
async def admin_login(req: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with username + password + master password to get admin token"""
    # Vérifier le master password
    if req.master_password != settings.MASTER_PASSWORD:
        raise HTTPException(403, "Invalid master password")
    
    # Vérifier l'utilisateur et son mot de passe
    from src.server.core.auth_utils import verify_password
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    # Vérifier que l'utilisateur a un rôle admin ou superadmin
    if user.role not in ("admin", "superadmin"):
        raise HTTPException(403, "User must be admin or superadmin")
    
    # Créer un token JWT
    token = create_token(user.id, user.username, user.role)
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    total_users     = (await db.execute(select(func.count(User.id)))).scalar()
    active_users    = (await db.execute(select(func.count(User.id)).where(User.active == True))).scalar()
    total_licenses  = (await db.execute(select(func.count(License.id)))).scalar()
    active_licenses = (await db.execute(select(func.count(License.id)).where(License.active == True))).scalar()
    used_licenses   = (await db.execute(select(func.count(License.id)).where(License.used_by != ""))).scalar()
    online_now      = len(manager.connections)
    voice_now       = len(manager.voice_room)
    return {
        "total_users":     total_users,
        "active_users":    active_users,
        "total_licenses":  total_licenses,
        "active_licenses": active_licenses,
        "used_licenses":   used_licenses,
        "free_licenses":   active_licenses - used_licenses,
        "online_now":      online_now,
        "voice_now":       voice_now,
    }


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    r = await db.execute(select(User).order_by(User.id))
    return [_user_dict(u) for u in r.scalars().all()]


@router.get("/users/public")
async def list_users_public(db: AsyncSession = Depends(get_db)):
    """Public endpoint for all users to view rankings (read-only)."""
    r = await db.execute(select(User).order_by(User.id))
    return [_user_dict_public(u) for u in r.scalars().all()]


class UserPatch(BaseModel):
    active:      Optional[bool] = None
    role:        Optional[str]  = None
    rank:        Optional[str]  = None
    rank_points: Optional[int]  = None


@router.patch("/users/{user_id}")
async def patch_user(
    user_id: int, req: UserPatch,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Restriction: seul les superadmins peuvent désactiver des comptes
    if req.active is not None and req.active == False:
        # Vérifier que l'utilisateur actuel est superadmin
        if current_admin.get("role") != "superadmin":
            raise HTTPException(403, "Only superadmins can deactivate accounts")
        # Empêcher la désactivation de superadmins
        if user.role == "superadmin":
            raise HTTPException(403, "Cannot deactivate superadmin accounts")
    
    # Restriction: seul les superadmins peuvent modifier les rôles
    if req.role is not None and current_admin.get("role") != "superadmin":
        raise HTTPException(403, "Only superadmins can change user roles")
    
    if req.active is not None:
        user.active = req.active
    if req.role is not None:
        if req.role not in ("user", "admin", "superadmin"):
            raise HTTPException(400, "Invalid role")
        user.role = req.role
    if req.rank is not None:
        user.rank = req.rank
    if req.rank_points is not None:
        user.rank_points = req.rank_points
    await db.commit()
    await db.refresh(user)
    # Broadcast updates
    await manager.broadcast({
        "type": "rank_update",
        "user_id": str(user_id),
        "role": user.role,
        "rank": user.rank,
        "rank_points": user.rank_points,
    })
    return _user_dict(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_superadmin),
):
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    # Empêcher la suppression de superadmins
    if user.role == "superadmin":
        raise HTTPException(403, "Cannot delete superadmin accounts")
    # Free their license
    if user.license_key:
        lic_r = await db.execute(select(License).where(License.key == user.license_key))
        lic = lic_r.scalar_one_or_none()
        if lic:
            lic.used_by = ""
    await db.delete(user)
    await db.commit()
    return {"deleted": user_id}


# ── Licenses ──────────────────────────────────────────────────────────────────

@router.get("/licenses")
async def list_licenses(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    r = await db.execute(select(License).order_by(License.id))
    return [_lic_dict(l) for l in r.scalars().all()]


class LicenseCreate(BaseModel):
    role:  str = "user"
    count: int = 1


@router.post("/licenses/generate")
async def generate_licenses(
    req: LicenseCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_superadmin),
):
    if req.role not in ("user", "admin", "superadmin"):
        raise HTTPException(400, "Invalid role")
    count = max(1, min(req.count, 100))
    keys = []
    for _ in range(count):
        key = "VLK-" + secrets.token_hex(6).upper()
        db.add(License(key=key, role=req.role, active=True))
        keys.append(key)
    await db.commit()
    return {"generated": keys, "count": len(keys)}


class LicensePatch(BaseModel):
    active: Optional[bool] = None
    role:   Optional[str]  = None


@router.patch("/licenses/{key}")
async def patch_license(
    key: str, req: LicensePatch,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_superadmin),
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
    return _lic_dict(lic)


@router.delete("/licenses/{key}")
async def delete_license(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_superadmin),
):
    r = await db.execute(select(License).where(License.key == key))
    lic = r.scalar_one_or_none()
    if not lic:
        raise HTTPException(404, "License not found")
    # Detach from user if in use
    if lic.used_by:
        ur = await db.execute(select(User).where(User.username == lic.used_by))
        u = ur.scalar_one_or_none()
        # We leave user intact but clear their license ref
    await db.delete(lic)
    await db.commit()
    return {"deleted": key}


# ── Announcements ─────────────────────────────────────────────────────────────

@router.get("/announcements")
async def list_announcements(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    r = await db.execute(select(Announcement).order_by(Announcement.created_at.desc()))
    return [_ann_dict(a) for a in r.scalars().all()]


class AnnouncementCreate(BaseModel):
    title:    str
    body:     str
    priority: str = "normal"


@router.post("/announcements")
async def create_announcement(
    req: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    if req.priority not in ("normal", "important", "urgent"):
        raise HTTPException(400, "Invalid priority")
    ann = Announcement(title=req.title, body=req.body, priority=req.priority)
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    await manager.broadcast({"type": "announcement", "data": _ann_dict(ann)})
    return _ann_dict(ann)


@router.delete("/announcements/{ann_id}")
async def delete_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    r = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = r.scalar_one_or_none()
    if not ann:
        raise HTTPException(404)
    ann.active = False
    await db.commit()
    return {"deleted": ann_id}


# ── Broadcast ─────────────────────────────────────────────────────────────────

class BroadcastMsg(BaseModel):
    content: str


@router.post("/broadcast")
async def broadcast_message(
    req: BroadcastMsg,
    _=Depends(get_current_admin),
):
    """Send a system chat message to all connected users."""
    await manager.broadcast({
        "type": "chat",
        "user_id": "0",
        "username": "⚙️ SYSTEM",
        "role": "superadmin",
        "content": req.content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_dict(u: User) -> dict:
    return {
        "id":               u.id,
        "username":         u.username,
        "roblox_username":  u.roblox_username,
        "role":             u.role,
        "rank":             u.rank,
        "rank_points":      u.rank_points,
        "avatar_url":       u.avatar_url,
        "license_key":      u.license_key,
        "active":           u.active,
        "created_at":       str(u.created_at),
        "last_seen":        str(u.last_seen),
    }


def _user_dict_public(u: User) -> dict:
    """Public user dict with limited information for normal users."""
    return {
        "id":               u.id,
        "username":         u.username,
        "rank":             u.rank,
        "rank_points":      u.rank_points,
        "avatar_url":       u.avatar_url,
        "active":           u.active,
    }


def _lic_dict(l: License) -> dict:
    return {
        "key":        l.key,
        "role":       l.role,
        "active":     l.active,
        "used_by":    l.used_by,
        "created_at": str(l.created_at),
    }


def _ann_dict(a: Announcement) -> dict:
    return {
        "id":         a.id,
        "title":      a.title,
        "body":       a.body,
        "priority":   a.priority,
        "active":     a.active,
        "created_at": str(a.created_at),
    }
