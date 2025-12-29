from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    id: str
    email: str
    created_at: datetime
    is_active: bool
    api_keys: Optional[List["APIKeyRead"]] = None  # List of API keys
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .api_key import APIKeyRead
        from .audit_log import AuditLogRead

    id: str
    email: str
    created_at: datetime
    is_active: bool
    api_keys: Optional[List["APIKeyRead"]] = None  # List of API keys
# For forward reference
from .api_key import APIKeyRead


class UserLogin(BaseModel):
    email: str
    password: str
