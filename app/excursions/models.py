from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.excursions.schemas import ExcursionDetailsScheme, ExcursionScheme, ItineraryItem
from app.models import Base


class ExcursionModel(Base):
    __tablename__ = "excursions"

    title: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    people_amount: Mapped[int] = mapped_column(nullable=False)
    people_left: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    image_url: Mapped[str] = mapped_column(nullable=False)
    bus_number: Mapped[int] = mapped_column(nullable=True, default=0)

    details: Mapped["ExcursionDetailsModel"] = relationship(
        "ExcursionDetailsModel",
        back_populates="excursion",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_read_model(self) -> ExcursionScheme:
        return ExcursionScheme(
            title=self.title,
            category=self.category,
            description=self.description,
            date=self.date,
            price=self.price,
            duration=self.duration,
            people_amount=self.people_amount,
            people_left=self.people_left,
            bus_number=self.bus_number,
            is_active=self.is_active,
            image_url=self.image_url,
            id=self.id,
        )


class ExcursionDetailsModel(Base):
    __tablename__ = "excursion_details"

    excursion_id: Mapped[int] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    inclusions: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    itinerary: Mapped[list[ItineraryItem]] = mapped_column(JSON, nullable=True)
    meeting_point: Mapped[str] = mapped_column(nullable=True)
    requirements: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=True)

    excursion: Mapped["ExcursionModel"] = relationship(
        "ExcursionModel", back_populates="details"
    )

    def to_read_model(self) -> ExcursionDetailsScheme:
        return ExcursionDetailsScheme(
            description=self.description,
            inclusions=self.inclusions,
            itinerary=self.itinerary,
            meeting_point=self.meeting_point,
            requirements=self.requirements,
            recommendations=self.recommendations,
            id=self.id,
            excursion_id=self.excursion_id,
        )
