from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./vlk.db"
    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION_VERY_LONG_SECRET"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    MASTER_PASSWORD: str = "vlk_admin_master_2024"
    VOICE_SERVICE: str = "livekit"  # livekit | mumble | webrtc
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    LIVEKIT_ROOM: str = ""
    MUMBLE_HOST: str = ""
    MUMBLE_PORT: str = ""
    WEBRTC_URL: str = ""

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()
