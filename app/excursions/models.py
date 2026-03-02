"""File with excursion models."""

from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.excursions.schemas import (
    ExcursionDetailsScheme,
    ExcursionImageSchema,
    ExcursionScheme,
    ExcursionType,
    ItineraryItem,
)
from app.models import Base


class ExcursionModel(Base):
    """Excursion model.

    Attributes:
        type: `ExcursionType`
        title: `str`
        description: `str`
        date: `datetime`
        price: `int`
        people_amount: `int`
        people_left: `int`
        is_active: `bool`
        bus_number: `int`
        cities: `list[str]`
        images: `list[ExcursionImageModel]`
        details: `ExcursionDetailsModel`
    """

    __tablename__ = "excursions"

    type: Mapped[ExcursionType] = mapped_column(
        Enum(ExcursionType), nullable=False, default=ExcursionType.EXCURSION
    )

    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    people_amount: Mapped[int] = mapped_column(nullable=False)
    people_left: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)
    bus_number: Mapped[int] = mapped_column(nullable=True, default=0)

    cities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=[])

    images: Mapped[list["ExcursionImageModel"]] = relationship(
        back_populates="excursion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    details: Mapped["ExcursionDetailsModel"] = relationship(
        "ExcursionDetailsModel",
        back_populates="excursion",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_read_model(self) -> ExcursionScheme:
        """Convert from excursion model to pydantic schema."""
        return ExcursionScheme(
            images=[image.to_read_model() for image in self.images],
            title=self.title,
            description=self.description,
            date=self.date,
            price=self.price,
            people_amount=self.people_amount,
            people_left=self.people_left,
            bus_number=self.bus_number,
            is_active=self.is_active,
            id=self.id,
            cities=list(self.cities),
            type=self.type,
        )

    def __repr__(self) -> str:
        """Excursion model representation."""
        return self.to_read_model().__repr__()


class ExcursionImageModel(Base):
    """Excursion image model.

    Arttributes:
        excursion_id: `int`
        url: `str`
    """

    __tablename__ = "excursion_images"

    excursion_id: Mapped[int] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(nullable=False)

    excursion: Mapped["ExcursionModel"] = relationship(back_populates="images")

    def to_read_model(self) -> ExcursionImageSchema:
        """Convert from excursion image model to pydantic schema."""
        return ExcursionImageSchema(
            id=self.id,
            excursion_id=self.excursion_id,
            url=self.url,
        )

    def __repr__(self) -> str:
        """Excursion image model representation."""
        return self.to_read_model().__repr__()


class ExcursionDetailsModel(Base):
    """Excursion details model.

    Attributes:
        excursion_id: `int`
        description: `str`
        inclusions: `list[str]`
        itinerary: `list[ItineraryItem]`
        meeting_point: `str`
        requirements: `list[str]`
        recommendations: `list[str]`
    """

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
        """Convert from excursion details model to pydantic schema."""
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

    def __repr__(self) -> str:
        """Excursion details model representation."""
        return self.to_read_model().__repr__()
