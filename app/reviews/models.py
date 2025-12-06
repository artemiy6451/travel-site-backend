from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import Base
from app.reviews.schemas import ReviewSchema


class ReviewModel(Base):
    __tablename__ = "reviews"

    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_read_model(self) -> ReviewSchema:
        return ReviewSchema(
            author_name=self.author_name,
            email=self.email,
            rating=self.rating,
            text=self.text,
            id=self.id,
            created_at=self.created_at,
            is_active=self.is_active,
        )
