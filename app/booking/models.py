from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.booking.schemas import BookingSchema, BookingStatus
from app.models import Base


class BookingModel(Base):
    __tablename__ = "bookings"

    excursion_id: Mapped[int] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    phone_number: Mapped[str] = mapped_column(nullable=False)

    total_people: Mapped[int] = mapped_column(nullable=False)
    children: Mapped[int] = mapped_column(nullable=True)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING
    )

    city: Mapped[str] = mapped_column(nullable=False, default="Симферополь")

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    changed_at: Mapped[datetime] = mapped_column(
        nullable=True,
        default=datetime.now,
        onupdate=datetime.now,
    )

    telegram_user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    telegram_message_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )

    def to_read_model(self) -> BookingSchema:
        return BookingSchema(
            id=self.id,
            excursion_id=self.excursion_id,
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,
            total_people=self.total_people,
            children=self.children,
            status=self.status,
            created_at=self.created_at,
            changed_at=self.changed_at,
            telegram_user_id=self.telegram_user_id,
            telegram_message_id=self.telegram_message_id,
            city=self.city,
        )
