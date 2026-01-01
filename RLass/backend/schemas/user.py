
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# Import these always so Pydantic model_rebuild works at runtime
from .api_key import APIKeyRead
from .usage_log import UsageLogRead
from .rate_limit import RateLimitConfigRead


class UserRead(BaseModel):
    id: str
    email: str
    created_at: datetime
    is_active: bool
    api_keys: Optional[List["APIKeyRead"]] = None
    usage_logs: Optional[List["UsageLogRead"]] = None
    rate_limits: Optional[List["RateLimitConfigRead"]] = None

    model_config = ConfigDict(from_attributes=True)

# Fix for PydanticUserError: ensure all referenced types are defined
UserRead.model_rebuild()

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
