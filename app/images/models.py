from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.images.schemas import ImageSchema
from app.models import Base

if TYPE_CHECKING:
    from app.excursions.models import ExcursionModel


class ImageModel(Base):
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

    def to_read_model(self) -> ImageSchema:
        """Convert from excursion image model to pydantic schema."""
        return ImageSchema(
            id=self.id,
            excursion_id=self.excursion_id,
            url=self.url,
        )

    def __repr__(self) -> str:
        """Excursion image model representation."""
        return self.to_read_model().__repr__()
