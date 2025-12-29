from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionBase(BaseModel):
    user_id: int
    session_token: str
    expires_at: datetime
    is_active: Optional[bool] = True

class SessionCreate(SessionBase):
    pass

class SessionRead(SessionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
