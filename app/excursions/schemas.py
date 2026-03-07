"""File with excursion schemas."""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


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


class ItineraryItem(BaseModel):
    """Item in itinerary."""

    time: str | None = None
    title: str
    description: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExcursionDetailsBaseScheme(BaseModel):
    """Base excursion details scheme."""

    description: str | None = None
    inclusions: List[str] | None = None
    itinerary: List[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: List[str] | None = None
    recommendations: List[str] | None = None


class ExcursionDetailsCreateScheme(ExcursionDetailsBaseScheme):
    """Create excursion details scheme."""

    pass


class ExcursionDetailsUpdateScheme(BaseModel):
    """Update excursion details scheme."""

    description: str | None = None
    inclusions: List[str] | None = None
    itinerary: List[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: List[str] | None = None
    recommendations: List[str] | None = None


class ExcursionDetailsScheme(ExcursionDetailsBaseScheme):
    """Excursion details scheme."""

    id: int
    excursion_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExcursionImageSchema(BaseModel):
    """Excursion image schema."""

    id: int
    excursion_id: int
    url: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExcursionScheme(ExcursionBaseScheme):
    """Excursion schema."""

    id: int

    images: list[ExcursionImageSchema] | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExcursionFullScheme(ExcursionScheme):
    """Full excursion scheme."""

    details: ExcursionDetailsScheme | None = None
    images: list[ExcursionImageSchema] | None = None
