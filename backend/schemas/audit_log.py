from pydantic import BaseModel
from typing import Optional
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

class AuditLogQuery(BaseModel):
    actor_id: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    event_type: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
