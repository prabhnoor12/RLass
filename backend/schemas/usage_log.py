from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UsageLogRead(BaseModel):
    id: str
    api_key: str
    endpoint: Optional[str] = None
    identifier: str
    timestamp: datetime
    status: str
    api_key_info: Optional["APIKeyRead"] = None
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .api_key import APIKeyRead

class UsageLogQuery(BaseModel):
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    identifier: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
