from pydantic import BaseModel
from datetime import datetime

class AccessLogBase(BaseModel):
    user_id: int
    garage_id: int
    action: str
    status: str

class AccessLogCreate(AccessLogBase):
    pass

class AccessLog(AccessLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True