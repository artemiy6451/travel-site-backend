from database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    excursion_id = Column(
        Integer, ForeignKey("excursions.id"), nullable=True, index=True
    )
    author_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_approved = Column(Boolean, default=False)  # прошел модерацию
    is_active = Column(Boolean, default=True)  # не скрыт

    # Связь с экскурсией (опционально)
    excursion = relationship("Excursion", back_populates="reviews")
