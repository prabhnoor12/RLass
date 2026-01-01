from sqlalchemy import Column, String, DateTime, ForeignKey
 
from typing import Optional
from datetime import datetime, UTC


from sqlalchemy.orm import relationship
from backend.database import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String, primary_key=True, index=True)
    api_key = Column(String, ForeignKey("api_keys.key"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String, nullable=True, index=True)
    identifier = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    status = Column(String, nullable=False)

    api_key_obj = relationship("APIKey", back_populates="usage_logs")
    user = relationship("User", back_populates="usage_logs")
