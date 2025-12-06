from datetime import datetime
from typing import List

from pydantic import BaseModel


class ExcursionBaseScheme(BaseModel):
    title: str
    category: str
    description: str
    date: datetime
    price: int
    duration: int
    people_amount: int
    people_left: int
    bus_number: int = 0
    is_active: bool
    image_url: str


class ExcursionCreateScheme(ExcursionBaseScheme):
    pass


class ExcursionUpdateScheme(BaseModel):
    title: str | None
    category: str | None
    description: str | None
    date: datetime | None
    price: int | None
    duration: int | None
    people_amount: int | None
    people_left: int | None
    is_active: bool | None
    bus_number: int | None
    image_url: str | None


class ExcursionScheme(ExcursionBaseScheme):
    id: int

    class Config:
        from_attributes = True


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


class ExcursionFullScheme(ExcursionScheme):
    details: ExcursionDetailsScheme | None = None
