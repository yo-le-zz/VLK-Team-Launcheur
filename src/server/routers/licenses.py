import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from src.server.core.database import get_db, License
from src.server.core.auth_utils import require_role

router = APIRouter()

class LicenseCreate(BaseModel):
    role: str = "user"
    count: int = 1

class LicensePatch(BaseModel):
    active: bool = None
    role: str = None

@router.get("/")
async def list_licenses(payload=Depends(require_role("admin","superadmin")), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(License))
    return [_lic(l) for l in r.scalars().all()]

@router.post("/generate")
async def generate_licenses(req: LicenseCreate, payload=Depends(require_role("admin","superadmin")), db: AsyncSession = Depends(get_db)):
    keys = []
    for _ in range(min(req.count, 50)):
        key = "VLK-" + secrets.token_hex(6).upper()
        db.add(License(key=key, role=req.role))
        keys.append(key)
    await db.commit()
    return {"generated": keys}

@router.patch("/{key}")
async def patch_license(key: str, req: LicensePatch, payload=Depends(require_role("admin","superadmin")), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(License).where(License.key == key))
    lic = r.scalar_one_or_none()
    if not lic:
        raise HTTPException(404)
    if req.active is not None:
        lic.active = req.active
    if req.role is not None:
        lic.role = req.role
    await db.commit()
    return _lic(lic)

@router.delete("/{key}")
async def delete_license(key: str, payload=Depends(require_role("superadmin")), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(License).where(License.key == key))
    lic = r.scalar_one_or_none()
    if not lic:
        raise HTTPException(404)
    await db.delete(lic)
    await db.commit()
    return {"deleted": key}

def _lic(l: License) -> dict:
    return {"key": l.key, "role": l.role, "active": l.active, "used_by": l.used_by, "created_at": str(l.created_at)}
