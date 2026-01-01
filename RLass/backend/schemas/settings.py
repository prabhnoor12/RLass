from pydantic import BaseModel
from pydantic import ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
