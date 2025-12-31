from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MaintenanceTaskBase(BaseModel):
    name: str
    status: Optional[str] = "pending"
    last_run: Optional[datetime] = None
    is_active: Optional[bool] = True

class MaintenanceTaskCreate(MaintenanceTaskBase):
    pass

class MaintenanceTaskRead(MaintenanceTaskBase):
    id: int

    class Config:
        orm_mode = True
