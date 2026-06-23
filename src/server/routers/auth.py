import secrets
import os
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from src.server.core.database import get_db, User, License
from src.server.core.auth_utils import hash_password, verify_password, create_token, decode_token, require_role
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
bearer = HTTPBearer()

class RegisterRequest(BaseModel):
    license_key: str
    username: str
    password: str
    roblox_username: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class ProfileUpdate(BaseModel):
    roblox_username: str = None
    avatar_url: str = None
    new_license_key: str = None

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(License).where(License.key == req.license_key, License.active == True))
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(400, "Invalid or inactive license key")
    if lic.used_by and lic.used_by != req.username:
        raise HTTPException(400, "License already in use")
    result2 = await db.execute(select(User).where(User.username == req.username))
    if result2.scalar_one_or_none():
        raise HTTPException(400, "Username already taken")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        license_key=req.license_key,
        roblox_username=req.roblox_username,
        role=lic.role,
    )
    db.add(user)
    lic.used_by = req.username
    await db.commit()
    await db.refresh(user)
    token = create_token(user.id, user.username, user.role)
    return {"token": token, "user": _user_dict(user)}

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not user.active:
        raise HTTPException(403, "Account disabled")
    token = create_token(user.id, user.username, user.role)
    return {"token": token, "user": _user_dict(user)}

@router.get("/me")
async def me(creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(401, "Invalid token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return _user_dict(user)

@router.patch("/profile")
async def update_profile(req: ProfileUpdate, creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(401)
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)
    if req.roblox_username is not None:
        user.roblox_username = req.roblox_username
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    if req.new_license_key:
        result2 = await db.execute(select(License).where(License.key == req.new_license_key, License.active == True))
        lic = result2.scalar_one_or_none()
        if not lic or (lic.used_by and lic.used_by != user.username):
            raise HTTPException(400, "Invalid license")
        # free old license
        old = await db.execute(select(License).where(License.key == user.license_key))
        old_lic = old.scalar_one_or_none()
        if old_lic:
            old_lic.used_by = ""
        user.license_key = req.new_license_key
        user.role = lic.role
        lic.used_by = user.username
    await db.commit()
    await db.refresh(user)
    return _user_dict(user)

@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    """Upload avatar image and return base64 encoded URL."""
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(401)
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are allowed")
    
    # Read file and convert to base64
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(400, "File too large (max 5MB)")
    
    # Encode to base64
    encoded = base64.b64encode(contents).decode()
    data_url = f"data:{file.content_type};base64,{encoded}"
    
    # Update user avatar
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404)
    
    user.avatar_url = data_url
    await db.commit()
    await db.refresh(user)
    
    return {"avatar_url": data_url}

def _user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "roblox_username": u.roblox_username,
        "role": u.role,
        "rank": u.rank,
        "rank_points": u.rank_points,
        "avatar_url": u.avatar_url,
        "license_key": u.license_key,
        "active": u.active,
    }
