from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"

settings = Settings()
