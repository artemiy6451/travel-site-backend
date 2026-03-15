"""File with excursion models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, TIMESTAMP, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.excursions.schemas import (
    ExcursionScheme,
    ExcursionType,
)
from app.models import Base

if TYPE_CHECKING:
    from app.details.models import DetailsModel
    from app.images.models import ImageModel


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

    images: Mapped[list["ImageModel"]] = relationship(
        "ImageModel",
        back_populates="excursion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    details: Mapped["DetailsModel"] = relationship(
        "DetailsModel",
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
