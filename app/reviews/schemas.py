from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class ReviewBase(BaseModel):
    excursion_id: Optional[int] = None
    author_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    rating: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=1, max_length=2000)

    @field_validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Текст отзыва не может быть пустым")
        return v.strip()


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = Field(None, min_length=1, max_length=2000)


class ReviewInDB(ReviewBase):
    id: int
    created_at: datetime
    is_approved: bool
    is_active: bool

    class Config:
        from_attributes = True


class ReviewPublic(ReviewInDB):
    pass


class ReviewAdmin(ReviewInDB):
    email: EmailStr
