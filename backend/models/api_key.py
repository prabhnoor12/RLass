from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
 
from datetime import datetime, UTC
from typing import Optional


from sqlalchemy.orm import relationship
from backend.database import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    key = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_used = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
    rate_limits = relationship("RateLimitConfig", back_populates="api_key_obj", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="api_key_obj", cascade="all, delete-orphan")
