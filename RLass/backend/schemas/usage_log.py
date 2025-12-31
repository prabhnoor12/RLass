from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .api_key import APIKeyRead
    from .user import UserRead

class UsageLogRead(BaseModel):
    id: str
    api_key: str
    customer_id: Optional[str] = None
    endpoint: Optional[str] = None
    identifier: str
    timestamp: datetime
    status: str
    api_key_info: Optional["APIKeyRead"] = None
    user: Optional["UserRead"] = None

class UsageLogQuery(BaseModel):
    api_key: Optional[str] = None
    customer_id: Optional[str] = None
    endpoint: Optional[str] = None
    identifier: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
