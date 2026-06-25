from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from datetime import datetime, timezone
from src.server.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    license_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    roblox_username: Mapped[str] = mapped_column(String(64), default="")
    role: Mapped[str] = mapped_column(String(16), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[str] = mapped_column(String(512), default="")
    rank: Mapped[str] = mapped_column(String(32), default="Recruit")
    rank_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class License(Base):
    __tablename__ = "licenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    used_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    body: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # seed default admin license and user
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from src.server.core.auth_utils import hash_password

        # Create default admin license
        result = await session.execute(select(License).where(License.key == "VLK-ADMIN-0000"))
        if not result.scalar_one_or_none():
            session.add(License(key="VLK-ADMIN-0000", role="superadmin", active=True))

        # Create default admin user
        result = await session.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            session.add(User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                license_key="VLK-ADMIN-0000",
                role="superadmin",
                active=True,
                roblox_username="",
                avatar_url="",
                rank="Legend",
                rank_points=1000
            ))
        else:
            # Update existing admin user with default values if they are empty
            if not admin_user.rank or admin_user.rank == "":
                admin_user.rank = "Legend"
            if admin_user.rank_points is None or admin_user.rank_points == 0:
                admin_user.rank_points = 1000
            if not admin_user.roblox_username:
                admin_user.roblox_username = ""
            if not admin_user.avatar_url:
                admin_user.avatar_url = ""

        await session.commit()
