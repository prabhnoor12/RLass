from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UsageStatsBase(BaseModel):
    user_id: int
    endpoint: str
    count: int
    period: str
    timestamp: Optional[datetime] = None

class UsageStatsCreate(UsageStatsBase):
    pass

class UsageStatsRead(UsageStatsBase):
    id: int

    class Config:
        orm_mode = True
