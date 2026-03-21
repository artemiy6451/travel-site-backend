"""File with user models."""

from datetime import datetime

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
    phone_number: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    email_confirmed_at: Mapped[datetime] = mapped_column(default=datetime.now)
    phone_confirmed_at: Mapped[datetime | None] = mapped_column(default=None)

    def to_read_model(self) -> UserSchema:
        """Convert from user model to pydantic schema."""
        return UserSchema(
            email=self.email,
            phone_number=self.phone_number,
            first_name=self.first_name,
            last_name=self.last_name,
            id=self.id,
            is_active=self.is_active,
            is_superuser=self.is_superuser,
            email_confirmed_at=self.email_confirmed_at,
            phone_confirmed_at=self.phone_confirmed_at,
        )

    def __repr__(self) -> str:
        """User model representation."""
        return self.to_read_model().__repr__()
