from pydantic import BaseModel
from typing import Optional

class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    rate_limit: int
    is_active: Optional[bool] = True

class PlanCreate(PlanBase):
    pass

class PlanRead(PlanBase):
    id: int

    model_config = {
        "from_attributes": True
    }
