from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.garage import GarageState, GarageAction

class WSMessage(BaseModel):
    type: str
    timestamp: datetime

class WSCommand(WSMessage):
    action: GarageAction

class WSStatus(WSMessage):
    state: GarageState
    garage_id: str

class WSStateUpdate(WSMessage):
    garage_id: str
    state: GarageState