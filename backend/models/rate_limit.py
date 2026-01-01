from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
 
from typing import Optional


from sqlalchemy.orm import relationship
from backend.database import Base


class RateLimitConfig(Base):
    __tablename__ = "rate_limit_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    api_key = Column(String, ForeignKey("api_keys.key"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String, nullable=True, index=True)
    limit = Column(Integer, nullable=False)
    period_seconds = Column(Integer, nullable=False)

        # No datetime fields in this model, so no changes needed

    api_key_obj = relationship("APIKey", back_populates="rate_limits")
    user = relationship("User", back_populates="rate_limits")
