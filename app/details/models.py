from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.details.schemas import DetailsScheme, ItineraryItem
from app.models import Base

if TYPE_CHECKING:
    from app.excursions.models import ExcursionModel


class DetailsModel(Base):
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

    def to_read_model(self) -> DetailsScheme:
        """Convert from excursion details model to pydantic schema."""
        return DetailsScheme(
            id=self.id,
            description=self.description,
            inclusions=self.inclusions,
            itinerary=self.itinerary,
            meeting_point=self.meeting_point,
            requirements=self.requirements,
            recommendations=self.recommendations,
            excursion_id=self.excursion_id,
        )

    def __repr__(self) -> str:
        """Excursion details model representation."""
        return self.to_read_model().__repr__()
