from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    telegram_id: str
    username: Optional[str] = None

class UserCreate(UserBase):
    pass

class TelegramAuth(BaseModel):
    id: str
    first_name: Optional[str]
    username: Optional[str]
    photo_url: Optional[str]
    auth_date: int
    hash: str

class User(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        orm_mode = True