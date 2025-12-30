from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base
from typing import Optional


from sqlalchemy.orm import relationship
from database import Base


class RateLimitConfig(Base):
    __tablename__ = "rate_limit_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    api_key = Column(String, ForeignKey("api_keys.key"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String, nullable=True, index=True)
    limit = Column(Integer, nullable=False)
    period_seconds = Column(Integer, nullable=False)
    # New: allow per-user and per-endpoint customizations
    custom_for_user = Column(Boolean, default=False)  # True if this is a user-specific override
    custom_for_endpoint = Column(Boolean, default=False)  # True if this is an endpoint-specific override

    api_key_obj = relationship("APIKey", back_populates="rate_limits")
    user = relationship("User", back_populates="rate_limits")
