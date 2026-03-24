from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.notifications.schemas import NotificationBaseSchema


class NotificationModel(Base):

    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    def to_read_model(self) -> NotificationBaseSchema:
        return NotificationBaseSchema(
            id=self.id,
            user_id=self.user_id,
            type=self.type,
            message=self.message,
            is_read=self.is_read,
            created_at=self.created_at,
        )
