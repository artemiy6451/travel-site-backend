"""File with excursion schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.images.schemas import ImageSchema


class ExcursionType(Enum):
    """Enum with excursion types."""

    EXCURSION = "excursion"
    TOUR = "tour"


class ExcursionBaseScheme(BaseModel):
    """Base excursion scheme."""

    type: ExcursionType
    title: str
    description: str
    date: datetime
    price: int
    people_amount: int
    people_left: int
    bus_number: int = 0
    is_active: bool

    cities: list[str]


class ExcursionCreateScheme(ExcursionBaseScheme):
    """Create excursion scheme."""

    pass


class ExcursionUpdateScheme(BaseModel):
    """Update excursion scheme."""

    type: ExcursionType
    title: str | None
    description: str | None
    date: datetime | None
    price: int | None
    people_amount: int | None
    people_left: int | None
    is_active: bool | None
    bus_number: int | None

    cities: list[str]


class ExcursionScheme(ExcursionBaseScheme):
    """Excursion schema."""

    id: int
    images: list[ImageSchema]

    class Config:
        """Pydantic config."""

        from_attributes = True
