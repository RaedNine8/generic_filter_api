from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    isbn = Column(String(20), unique=True, nullable=False)
    genre = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    pages = Column(Integer, nullable=True)
    published_year = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    # Foreign key to author
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    
    # Relationship to author
    author = relationship("Author", back_populates="books")
