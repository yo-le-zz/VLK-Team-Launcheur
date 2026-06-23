from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from src.server.core.database import get_db, Announcement
from src.server.core.config import settings
from src.server.core.ws_manager import manager

router = APIRouter()

def check_master(x_master_password: str = Header(None)):
    if x_master_password != settings.MASTER_PASSWORD:
        raise HTTPException(403)

class AnnouncementCreate(BaseModel):
    title: str
    body: str
    priority: str = "normal"

@router.get("/")
async def get_announcements(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Announcement).where(Announcement.active == True).order_by(Announcement.created_at.desc()).limit(10))
    return [_ann(a) for a in r.scalars().all()]

@router.post("/")
async def create_announcement(req: AnnouncementCreate, db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    ann = Announcement(title=req.title, body=req.body, priority=req.priority)
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    await manager.broadcast({"type": "announcement", "data": _ann(ann)})
    return _ann(ann)

@router.delete("/{ann_id}")
async def delete_announcement(ann_id: int, db: AsyncSession = Depends(get_db), _=Depends(check_master)):
    r = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = r.scalar_one_or_none()
    if not ann:
        raise HTTPException(404)
    ann.active = False
    await db.commit()
    return {"ok": True}

def _ann(a: Announcement) -> dict:
    return {"id": a.id, "title": a.title, "body": a.body, "priority": a.priority, "created_at": str(a.created_at)}
