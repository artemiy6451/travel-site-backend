from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class ReviewBase(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    rating: int = Field(..., ge=1, le=5)
    text: str = Field(..., min_length=1, max_length=2000)

    @field_validator("text")
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Текст отзыва не может быть пустым")
        return v.strip()


class ReviewCreate(ReviewBase):
    pass


class ReviewSchema(ReviewBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ReviewAdmin(ReviewSchema):
    email: EmailStr
