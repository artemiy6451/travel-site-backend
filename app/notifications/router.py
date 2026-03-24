from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, WebSocket, status

from app.auth.depends import get_current_user, require_superuser
from app.auth.service import AuthService
from app.notifications.depends import get_notification_service
from app.notifications.exceptions import NotificationNotFoundError
from app.notifications.schemas import (
    BulkNotificationSchema,
    BulkReminderSchema,
    CreateNotificationSchema,
    NotificationBaseSchema,
    UpdateNotificationSchema,
)
from app.notifications.service import NotificationService
from app.user.schemas import UserSchema

notifications_router = APIRouter(tags=["Notifications"])


@notifications_router.post(
    "/notifications",
    response_model=NotificationBaseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    notification: CreateNotificationSchema,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> NotificationBaseSchema:
    return await service.create_notification(notification)


@notifications_router.post(
    "/notifications/bulk-by-phone",
    response_model=list[NotificationBaseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_notifications_for_users(
    payload: BulkNotificationSchema,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[NotificationBaseSchema]:
    return await service.notify_users_by_phone(payload)


@notifications_router.post(
    "/notifications/reminders/bulk",
    response_model=list[NotificationBaseSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_reminders_for_users(
    payload: BulkReminderSchema,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[NotificationBaseSchema]:
    return await service.notify_users_reminder(payload)


@notifications_router.get(
    "/notifications/unread",
    response_model=list[NotificationBaseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_unread_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[NotificationBaseSchema]:
    return await service.get_unread_notifications(current_user.id)


@notifications_router.post(
    "/notifications/{notification_id}/read",
    response_model=NotificationBaseSchema,
    status_code=status.HTTP_200_OK,
)
async def mark_notification_as_read(
    notification_id: int,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> NotificationBaseSchema:
    data = UpdateNotificationSchema(
        id=notification_id, user_id=current_user.id, is_read=True
    )
    try:
        return await service.mark_as_read(data)
    except NotificationNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@notifications_router.websocket("/ws/notifications")
async def notifications_ws(
    websocket: WebSocket,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session_id: Annotated[str | None, Cookie(alias="session_id")] = None,
) -> None:
    if session_id is None:
        await websocket.close(code=1008)
        return

    auth_service = AuthService()
    try:
        user = await auth_service.get_user_by_session(session_id)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await service.handle_websocket(websocket, user)
