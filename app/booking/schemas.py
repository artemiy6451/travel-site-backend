import enum
from datetime import datetime

from pydantic import BaseModel


class BookingStatus(enum.Enum):
    """Статусы бронирования"""

    PENDING = "pending"  # Ожидает подтверждения
    CONFIRMED = "confirmed"  # Подтверждена
    CANCELLED = "cancelled"  # Отменена
    EXPIRED = "expired"  # Просрочена (не подтвердили вовремя)


class BookingCreate(BaseModel):
    excursion_id: int
    first_name: str
    last_name: str
    phone_number: str

    total_people: int
    children: int | None = None

    city: str


class BookingSchema(BookingCreate):
    id: int
    status: BookingStatus

    created_at: datetime
    changed_at: datetime

    telegram_user_id: int | None
    telegram_message_id: int | None

    class Config:
        from_attributes = True
