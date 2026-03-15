from pydantic import BaseModel


class ItineraryItem(BaseModel):
    """Item in itinerary."""

    time: str | None = None
    title: str
    description: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class DetailsBaseScheme(BaseModel):
    """Base excursion details scheme."""

    description: str | None = None
    inclusions: list[str] | None = None
    itinerary: list[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: list[str] | None = None
    recommendations: list[str] | None = None


class DetailsCreateScheme(DetailsBaseScheme):
    """Create excursion details scheme."""

    pass


class DetailsUpdateScheme(BaseModel):
    """Update excursion details scheme."""

    description: str | None = None
    inclusions: list[str] | None = None
    itinerary: list[ItineraryItem] | None = None
    meeting_point: str | None = None
    requirements: list[str] | None = None
    recommendations: list[str] | None = None


class DetailsScheme(DetailsBaseScheme):
    """Excursion details scheme."""

    id: int
    excursion_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True
