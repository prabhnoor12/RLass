from pydantic import BaseModel
from typing import Optional

class CheckRequest(BaseModel):
    api_key: str
    identifier: str  # e.g., user ID or IP
    endpoint: Optional[str] = None
    api_key_info: Optional["APIKeyRead"] = None
    # For forward reference
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .api_key import APIKeyRead

class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    reset: int  # Unix timestamp for when the limit resets
    message: Optional[str] = None
