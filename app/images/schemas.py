from pydantic import BaseModel


class ImageSchema(BaseModel):
    """Excursion image schema."""

    id: int
    excursion_id: int
    url: str

    class Config:
        """Pydantic config."""

        from_attributes = True
