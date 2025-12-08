from pydantic import BaseModel


class BookingCreate(BaseModel):
    excursion_id: int
    first_name: str
    last_name: str
    phone_number: str
    total_people: int
    children: int | None = None


class BookingSchema(BookingCreate):
    is_active: bool
    id: int

    class Config:
        from_attributes = True
