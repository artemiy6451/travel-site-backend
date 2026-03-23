from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.depends import get_current_user
from app.notifications.depends import get_notification_service
from app.notifications.schemas import CreateNotificationSchema, NotificationBaseSchema
from app.notifications.service import NotificationService
from app.user.schemas import UserSchema

notifications_router = APIRouter(tags=["Notifications"])


@notifications_router.get("/notifications/create")
async def create_notification(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    notification: CreateNotificationSchema,
    _: Annotated[UserSchema, Depends(get_current_user)],
) -> NotificationBaseSchema:
    return await service.create_notification(notification)
