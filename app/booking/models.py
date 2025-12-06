from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Booking(Base):
    __tablename__ = "bookings"

    excursion_id: Mapped[str] = mapped_column(nullable=False)

    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    phone_number: Mapped[str] = mapped_column(nullable=False)

    total_people: Mapped[int] = mapped_column(nullable=False)
    children: Mapped[int] = mapped_column(nullable=True)
