from app.database import async_session_maker
from app.notifications.exceptions import NotificationNotFoundError
from app.notifications.model import NotificationModel
from app.notifications.schemas import CreateNotificationSchema, NotificationBaseSchema
from app.repository import SQLAlchemyRepository


class NotificationService:
    def __init__(self) -> None:
        self.notifications_repository: SQLAlchemyRepository[NotificationModel] = (
            SQLAlchemyRepository(async_session_maker, NotificationModel)
        )

    async def create_notification(
        self, notification: CreateNotificationSchema
    ) -> NotificationBaseSchema:
        new_notification = await self.notifications_repository.add_one(
            notification.model_dump()
        )
        return new_notification.to_read_model()

    async def get_notification(self) -> NotificationBaseSchema:
        notification = await self.notifications_repository.find_one(
            NotificationModel.is_read == False  # noqa: E712
        )
        if notification is None:
            raise NotificationNotFoundError
        return notification.to_read_model()
