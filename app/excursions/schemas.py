from datetime import datetime
from typing import List, Optional

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
    image_url: str | None


class ExcursionScheme(ExcursionBaseScheme):
    id: int

    class Config:
        from_attributes = True


class ItineraryItem(BaseModel):
    time: Optional[str] = None
    title: str
    description: Optional[str] = None


class ExcursionDetailsBaseScheme(BaseModel):
    description: Optional[str] = None  # полное описание маршрута
    inclusions: Optional[List[str]] = None  # что входит
    itinerary: Optional[List[ItineraryItem]] = None  # пошаговая программа
    meeting_point: Optional[str] = None  # место сбора
    requirements: Optional[List[str]] = None  # требования
    recommendations: Optional[List[str]] = None  # рекомендации


class ExcursionDetailsCreateScheme(ExcursionDetailsBaseScheme):
    pass


class ExcursionDetailsUpdateScheme(BaseModel):
    description: Optional[str] = None
    inclusions: Optional[List[str]] = None
    itinerary: Optional[List[ItineraryItem]] = None
    meeting_point: Optional[str] = None
    requirements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class ExcursionDetailsScheme(ExcursionDetailsBaseScheme):
    id: int
    excursion_id: int

    class Config:
        from_attributes = True


class ExcursionFullScheme(ExcursionScheme):
    details: Optional[ExcursionDetailsScheme] = None
