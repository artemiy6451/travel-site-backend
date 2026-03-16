"""File with user models."""

from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.user.schemas import UserSchema


class UserModel(Base):
    """User model.

    Attributes:
        email: `str`
        phone_number: `str`
        hashed_password: `str`
        is_active: `bool`
        is_superuser: `bool`
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def to_read_model(self) -> UserSchema:
        """Convert from user model to pydantic schema."""
        return UserSchema(
            email=self.email,
            id=self.id,
            is_active=self.is_active,
            is_superuser=self.is_superuser,
        )

    def __repr__(self) -> str:
        """User model representation."""
        return self.to_read_model().__repr__()
