from pydantic import BaseModel
from typing import Optional

class UserSettingsBase(BaseModel):
    user_id: int
    key: str
    value: str
    is_active: Optional[bool] = True

class UserSettingsCreate(UserSettingsBase):
    pass

class UserSettingsRead(UserSettingsBase):
    id: int

    class Config:
        orm_mode = True
