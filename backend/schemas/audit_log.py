from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogRead(BaseModel):
    id: str
    action: str
    actor_id: str
    target: Optional[str] = None
    timestamp: datetime
    details: Optional[str] = None
    actor: Optional["UserRead"] = None
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .user import UserRead

class AuditLogQuery(BaseModel):
    actor_id: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
