from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from typing import Optional
from datetime import datetime


from sqlalchemy.orm import relationship
from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    action = Column(String, nullable=False)
    actor_id = Column(String, ForeignKey("users.id"), nullable=False)
    target = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)
    # New fields for security insights
    event_type = Column(String, nullable=True)  # e.g., 'key_usage', 'quota_change', 'admin_action'
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    actor = relationship("User", back_populates="audit_logs")
