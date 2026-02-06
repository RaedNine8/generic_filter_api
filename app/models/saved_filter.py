from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.database import Base


class SavedFilter(Base):
    __tablename__ = "saved_filters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False, index=True)
    filters = Column(JSON, nullable=False, default=list)
    sort_by = Column(String(100), nullable=True)
    sort_order = Column(String(4), default="asc")
    page_size = Column(Integer, default=10)
    search_query = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
