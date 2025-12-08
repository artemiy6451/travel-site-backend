from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.booking.schemas import BookingSchema
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
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)

    def to_read_model(self) -> BookingSchema:
        return BookingSchema(
            excursion_id=self.excursion_id,
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,
            total_people=self.total_people,
            children=self.children,
            is_active=self.is_active,
            id=self.id,
        )
