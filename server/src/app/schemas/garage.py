from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class GarageState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"

class GarageAction(str, Enum):
    OPEN = "open"
    CLOSE = "close"
    STOP = "stop"

class GarageBase(BaseModel):
    name: str
    esp32_identifier: str

class GarageCreate(GarageBase):
    pass

class GarageUpdate(BaseModel):
    name: Optional[str] = None
    is_approved: Optional[bool] = None

class GarageCommand(BaseModel):
    action: GarageAction

class GarageApproval(BaseModel):
    esp32_identifier: str
    name: str

class Garage(GarageBase):
    id: int
    current_state: GarageState
    is_approved: bool
    created_at: datetime

    class Config:
        orm_mode = True