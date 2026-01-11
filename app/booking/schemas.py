from datetime import datetime

from pydantic import BaseModel


class BookingCreate(BaseModel):
    excursion_id: int
    first_name: str
    last_name: str
    phone_number: str
    total_people: int
    children: int | None = None


class BookingSchema(BookingCreate):
    id: int
    is_active: bool
    created_at: datetime
    confirmed_at: datetime | None

    class Config:
        from_attributes = True
