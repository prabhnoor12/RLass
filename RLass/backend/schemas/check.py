
from pydantic import BaseModel
from typing import Optional

from .api_key import APIKeyRead

class CheckRequest(BaseModel):
    api_key: str
    identifier: str  # e.g., user ID or IP
    endpoint: Optional[str] = None
    api_key_info: Optional[APIKeyRead] = None

class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    reset: int  # Unix timestamp for when the limit resets
    message: Optional[str] = None
