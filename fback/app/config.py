from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Always resolve .env relative to this file's location (app/../.env)
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Portfolio Backend"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme-use-a-strong-secret-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/fback"

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"

    # JWT
    JWT_SECRET: str = "changeme-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Rate limiting
    CONTACT_RATE_LIMIT: str = "5/minute"
    ADMIN_RATE_LIMIT: str = "60/minute"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()