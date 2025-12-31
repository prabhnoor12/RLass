
from pydantic import BaseModel
from typing import Optional

class RateLimitConfigCreate(BaseModel):
    api_key: str
    customer_id: Optional[str] = None
    endpoint: Optional[str] = None
    limit: int
    period_seconds: int

class RateLimitConfigRead(BaseModel):
    api_key: str
    customer_id: Optional[str] = None
    endpoint: Optional[str] = None
    limit: int
    period_seconds: int

class RateLimitStatusRead(BaseModel):
    api_key: str
    identifier: str
    window_start: int
    count: int
