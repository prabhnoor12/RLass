from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from typing import Optional
from datetime import datetime


from sqlalchemy.orm import relationship
from ..database import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String, primary_key=True, index=True)
    api_key = Column(String, ForeignKey("api_keys.key"), nullable=False, index=True)
    endpoint = Column(String, nullable=True, index=True)
    identifier = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)

    api_key_obj = relationship("APIKey", back_populates="usage_logs")
