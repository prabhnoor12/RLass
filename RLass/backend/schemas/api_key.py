from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import UserRead
    from .rate_limit import RateLimitConfigRead
    from .usage_log import UsageLogRead


class APIKeyRead(BaseModel):
    key: str
    user_id: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None

    class Config:
        orm_mode = True

class APIKeyCreate(BaseModel):
    user_id: str

class APIKeyRevoke(BaseModel):
    key: str
