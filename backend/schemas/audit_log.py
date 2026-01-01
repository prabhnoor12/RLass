from pydantic import BaseModel, ConfigDict
from typing import Optional

# Import UserRead for use in AuditLogRead
from .user import UserRead
from .usage_log import UsageLogRead
from .api_key import APIKeyRead
from .rate_limit import RateLimitConfigRead
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

class AuditLogRead(BaseModel):
    id: str
    action: str
    actor_id: str
    target: Optional[str] = None
    timestamp: datetime
    details: Optional[str] = None
    actor: Optional["UserRead"] = None
    TYPE_CHECKING: ClassVar[bool] = False
    if TYPE_CHECKING:
        from .user import UserRead

    model_config = ConfigDict(from_attributes=True)


class AuditLogQuery(BaseModel):
    actor_id: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    event_type: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

# Fix for Pydantic forward references
AuditLogRead.model_rebuild()
