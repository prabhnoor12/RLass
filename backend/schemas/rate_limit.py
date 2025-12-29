from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_key import APIKeyRead

class RateLimitConfigCreate(BaseModel):
    api_key: str
    endpoint: Optional[str] = None
    limit: int
    period_seconds: int
    api_key_info: Optional["APIKeyRead"] = None

class RateLimitConfigRead(BaseModel):
    api_key: str
    endpoint: Optional[str] = None
    limit: int
    period_seconds: int

class RateLimitStatusRead(BaseModel):
    api_key: str
    identifier: str
    window_start: int
    count: int
    api_key_info: Optional["APIKeyRead"] = None
