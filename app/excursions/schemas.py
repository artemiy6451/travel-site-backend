from datetime import datetime
from typing import List

from pydantic import BaseModel


class ExcursionBaseScheme(BaseModel):
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
    pass


class ExcursionUpdateScheme(BaseModel):
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
    time: str | None = None
    title: str
    description: str | None = None

    class Config:
        from_attributes = True


class ExcursionDetailsBaseScheme(BaseModel):
    description: str | None = None
    inclusions: List[str] | None = None
    itinerary: List[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: List[str] | None = None
    recommendations: List[str] | None = None


class ExcursionDetailsCreateScheme(ExcursionDetailsBaseScheme):
    pass


class ExcursionDetailsUpdateScheme(BaseModel):
    description: str | None = None
    inclusions: List[str] | None = None
    itinerary: List[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: List[str] | None = None
    recommendations: List[str] | None = None


class ExcursionDetailsScheme(ExcursionDetailsBaseScheme):
    id: int
    excursion_id: int

    class Config:
        from_attributes = True


class ExcursionImageSchema(BaseModel):
    id: int
    excursion_id: int
    url: str

    class Config:
        from_attributes = True


class ExcursionScheme(ExcursionBaseScheme):
    id: int

    images: list[ExcursionImageSchema] | None

    class Config:
        from_attributes = True


class ExcursionFullScheme(ExcursionScheme):
    details: ExcursionDetailsScheme | None = None
    images: list[ExcursionImageSchema] | None = None
