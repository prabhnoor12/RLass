from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthTokenBase(BaseModel):
    user_id: int
    token: str
    expires_at: datetime
    is_active: Optional[bool] = True

class AuthTokenCreate(AuthTokenBase):
    pass

class AuthTokenRead(AuthTokenBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
