from pydantic import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Garage"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ADMIN_TELEGRAM_ID: str

    class Config:
        env_file = ".env"

settings = Settings()