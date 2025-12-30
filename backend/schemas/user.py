from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserRead(BaseModel):
    id: str
    email: str
    created_at: datetime
    is_active: bool
    api_keys: Optional[List["APIKeyRead"]] = None
    usage_logs: Optional[List["UsageLogRead"]] = None
    rate_limits: Optional[List["RateLimitConfigRead"]] = None
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .api_key import APIKeyRead
        from .usage_log import UsageLogRead
        from .rate_limit import RateLimitConfigRead

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
