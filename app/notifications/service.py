from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.booking.schemas import BookingSchema
from app.database import async_session_maker
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcursionService
from app.notifications.exceptions import NotificationNotFoundError
from app.notifications.manager import notifications_ws_manager
from app.notifications.model import NotificationModel
from app.notifications.schemas import (
    BulkNotificationSchema,
    BulkReminderSchema,
    CreateNotificationSchema,
    NotificationBaseSchema,
    UpdateNotificationSchema,
)
from app.repository import SQLAlchemyRepository
from app.user.models import UserModel
from app.user.schemas import UserSchema
from app.utils.redis_config import redis_client


class NotificationService:
    def __init__(self) -> None:
        self.notifications_repository: SQLAlchemyRepository[NotificationModel] = (
            SQLAlchemyRepository(async_session_maker, NotificationModel)
        )
        self.users_repository: SQLAlchemyRepository[UserModel] = SQLAlchemyRepository(
            async_session_maker, UserModel
        )
        self.excursion_service: ExcursionService = ExcursionService()

    async def create_notification(
        self, notification: CreateNotificationSchema
    ) -> NotificationBaseSchema:
        new_notification = await self.notifications_repository.add_one(
            notification.model_dump()
        )
        parsed = new_notification.to_read_model()
        self._cache_unread(parsed)
        await notifications_ws_manager.send_to_user(
            parsed.user_id,
            {"event": "notification", "data": parsed.model_dump(mode="json")},
        )
        return parsed

    async def get_unread_notifications(
        self, user_id: int
    ) -> list[NotificationBaseSchema]:
        cached = self._get_cached_unread(user_id)
        if cached:
            return cached

        notifications = await self.notifications_repository.find_all(
            filter_by=(NotificationModel.user_id == user_id)
            & (NotificationModel.is_read == False),  # noqa: E712
            order_by=NotificationModel.created_at,
        )
        parsed = [n.to_read_model() for n in notifications]
        for notification in parsed:
            self._cache_unread(notification)
        return parsed

    async def mark_as_read(
        self, data: UpdateNotificationSchema
    ) -> NotificationBaseSchema:
        updated = await self.notifications_repository.update(
            where=(NotificationModel.id == data.id)
            & (NotificationModel.user_id == data.user_id),
            data={"is_read": data.is_read},
        )
        if updated is None:
            raise NotificationNotFoundError

        self._remove_from_cache(user_id=data.user_id, notification_id=data.id)
        parsed = updated.to_read_model()
        await notifications_ws_manager.send_to_user(
            parsed.user_id, {"event": "read", "id": parsed.id}
        )
        return parsed

    async def notify_admins_about_booking(
        self, booking: BookingSchema, excursion: ExcursionScheme
    ) -> list[NotificationBaseSchema]:
        admins = await self._get_admin_users()
        if not admins:
            logger.warning("No admin users found to notify about booking {}", booking.id)
            return []

        notifications: list[NotificationBaseSchema] = []
        message = self._format_booking_message(booking, excursion)
        for admin in admins:
            payload = CreateNotificationSchema(
                user_id=admin.id,
                type="booking_create",
                message=message,
            )
            created = await self.create_notification(payload)
            notifications.append(created)
        return notifications

    async def notify_users_by_phone(
        self, data: BulkNotificationSchema
    ) -> list[NotificationBaseSchema]:
        if not data.phone_numbers:
            return []

        users = await self.users_repository.find_all(
            filter_by=UserModel.phone_number.in_(data.phone_numbers),
            limit=len(data.phone_numbers) or 100,
        )

        notifications: list[NotificationBaseSchema] = []
        for user in users:
            payload = CreateNotificationSchema(
                user_id=user.id, type=data.type, message=data.message
            )
            notifications.append(await self.create_notification(payload))

        if len(users) != len(set(data.phone_numbers)):
            logger.warning(
                "Some phone numbers were not found: requested={}, found={}",
                len(data.phone_numbers),
                len(users),
            )

        return notifications

    async def notify_users_reminder(
        self, data: BulkReminderSchema
    ) -> list[NotificationBaseSchema]:
        excursion = await self.excursion_service.get_excursion(data.excursion_id)
        message = self._format_reminder_message(excursion, data.days_before)
        payload = BulkNotificationSchema(
            phone_numbers=data.phone_numbers,
            message=message,
            type="booking_remainder",
        )
        return await self.notify_users_by_phone(payload)

    async def handle_websocket(self, websocket: WebSocket, user: UserSchema) -> None:
        """Manage lifecycle and messaging for notifications websocket."""
        await notifications_ws_manager.connect(user.id, websocket)
        try:
            await self._send_unread_to_socket(websocket, user.id)

            while True:
                payload = await websocket.receive_json()
                action = payload.get("action")

                if action == "read":
                    notification_id = payload.get("id") or payload.get("notification_id")
                    if notification_id is None:
                        await websocket.send_json(
                            {"event": "error", "detail": "notification id is required"}
                        )
                        continue

                    try:
                        await self.mark_as_read(
                            UpdateNotificationSchema(
                                id=int(notification_id),
                                user_id=user.id,
                                is_read=True,
                            )
                        )
                    except NotificationNotFoundError:
                        await websocket.send_json(
                            {"event": "error", "detail": "notification not found"}
                        )
                else:
                    await websocket.send_json(
                        {"event": "error", "detail": "Unknown action"}
                    )
        except WebSocketDisconnect:
            pass
        finally:
            notifications_ws_manager.disconnect(user.id, websocket)

    async def _send_unread_to_socket(self, websocket: WebSocket, user_id: int) -> None:
        unread = await self.get_unread_notifications(user_id)
        if not unread:
            return

        await websocket.send_json(
            {
                "event": "unread",
                "data": [
                    notification.model_dump(mode="json") for notification in unread
                ],
            }
        )

    def _redis_key(self, user_id: int) -> str:
        return f"notifications:user:{user_id}"

    def _cache_unread(self, notification: NotificationBaseSchema) -> None:
        try:
            redis_client.hset(
                self._redis_key(notification.user_id),
                str(notification.id),
                notification.model_dump_json(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to cache notification {}: {}", notification.id, exc)

    def _remove_from_cache(self, user_id: int, notification_id: int) -> None:
        try:
            redis_client.hdel(self._redis_key(user_id), str(notification_id))
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to remove notification {} from cache: {}", notification_id, exc
            )

    def _get_cached_unread(self, user_id: int) -> list[NotificationBaseSchema]:
        try:
            cached = redis_client.hgetall(self._redis_key(user_id))
            notifications: list[NotificationBaseSchema] = []
            for value in cached.values():  # type: ignore
                notifications.append(NotificationBaseSchema.model_validate_json(value))
            return sorted(notifications, key=lambda n: n.created_at)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to fetch cached notifications for user {}: {}", user_id, exc
            )
            return []

    async def _get_admin_users(self) -> list[UserModel]:
        admins = await self.users_repository.find_all(
            filter_by=UserModel.is_superuser == True  # noqa: E712
        )
        return admins

    @staticmethod
    def _format_booking_message(
        booking: BookingSchema, excursion: ExcursionScheme
    ) -> str:
        return (
            f"Новая бронь #{booking.id}: {booking.last_name} {booking.first_name}\n"
            f"Тел.: {booking.phone_number}\n"
            f"Город: {booking.city}\n"
            f"Гостей: {booking.total_people}, дети {booking.children or 0}\n"
            f'экскурсия "{excursion.title}"'
        )

    @staticmethod
    def _format_reminder_message(excursion: ExcursionScheme, days_before: int) -> str:
        days_before = (excursion.date - datetime.now()).days
        date_part = excursion.date.strftime("%d.%m.%Y %H:%M")
        city_part = excursion.cities[0] if excursion.cities else "уточните место встречи"
        return (
            f'Экскурсия "{excursion.title}" состоится {date_part}.\n'
            f"До поездки осталось {days_before} дн., место встречи: {city_part}.\n\n"
            f"Пожалуйста оплатите бронирование переводом по номеру телефона:"
            f"+7(978)700-58-59 Виталий (Т-банк).\n\n"
            f"Если вы увидели повторно данное уведомление, то просто проигнорируйте его."
        )
