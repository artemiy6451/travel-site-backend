from sqlalchemy.orm import Mapped, mapped_column

from app.auth.schemas import UserSchema
from app.models import Base


class UserModel(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def to_read_model(self) -> UserSchema:
        return UserSchema(
            email=self.email,
            id=self.id,
            is_active=self.is_active,
            is_superuser=self.is_superuser,
        )
