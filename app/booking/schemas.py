"""File with booking schemas."""

import enum
from datetime import datetime

from pydantic import BaseModel


class BookingStatus(enum.Enum):
    """Booking status.

    Attributes:
        PENDING: `str` = "pending"
        CONFIRMED: `str` = "confirmed"
        CANCELLED: `str` = "cancelled"
        EXPIRED: `str` = "expired"
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BookingCreate(BaseModel):
    """Booking create schema.

    Attributes:
        excursion_id: `int`
        first_name: `str`
        last_name: `str`
        phone_number: `str`

        total_people: `int`
        children: `int` | None = None

        city: `str`
    """

    excursion_id: int
    first_name: str
    last_name: str
    phone_number: str

    total_people: int
    children: int | None = None

    city: str


class BookingSchema(BookingCreate):
    """Booking schema.

    Attributes:
        id: `int`
        status: `BookingStatus`

        created_at: `datetime`
        changed_at: `datetime`

        telegram_user_id: `int | None`
        telegram_message_id: `int | None`
    """

    id: int
    status: BookingStatus

    created_at: datetime
    changed_at: datetime

    telegram_user_id: int | None
    telegram_message_id: int | None

    class Config:
        """Pydantic config."""

        from_attributes = True
