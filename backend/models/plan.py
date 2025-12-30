from sqlalchemy import Column, Integer, String, Boolean
from backend.database import Base

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    rate_limit = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
