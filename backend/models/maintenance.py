from sqlalchemy import Column, Integer, String, DateTime, Boolean
from ..database import Base
import datetime

class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")
    last_run = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
