from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import datetime

class APIKeyCreate(BaseModel):
    user_id: str

    key: str
    user_id: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    user: Optional["UserRead"] = None  # Nested user info
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .user import UserRead
        from .rate_limit import RateLimitConfigRead
        from .usage_log import UsageLogRead
# For forward reference
if TYPE_CHECKING:
    from .user import UserRead

class APIKeyRevoke(BaseModel):
    key: str
