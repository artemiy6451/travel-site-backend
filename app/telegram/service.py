from typing import List, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme


class TelegramService:
    def __init__(self) -> None:
        self.bot: Optional[Bot] = None
        self.notification_chat_ids: List[int] = []
        self._initialize_bot()

    def _initialize_bot(self) -> None:
        self.bot = Bot(
            token=settings.telegram_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

    def _get_keyboard(self, is_active: bool, booking_id: int) -> InlineKeyboardMarkup:
        logger.debug(
            "Generate keyboard with is_active={} and booking_id={}",
            is_active,
            booking_id,
        )
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"{'❌ Отменить' if is_active else '✅ Подтвердить'}",
                callback_data=f"toggle_booking:{booking_id}",
            )
        )
        return builder.as_markup()

    async def send_notification(
        self,
        excursion: ExcursionScheme,
        booking: BookingSchema,
    ) -> bool:
        logger.debug(
            "Send notification with excursion={} and booking={}",
            excursion,
            booking,
        )

        message = (
            "🎫 <b>НОВОЕ БРОНИРОВАНИЕ</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<b>ID:</b> <code>#{booking.id}</code>\n"
            f"<b>Экскурсия:</b> {excursion.title}\n"
            f"<b>Дата:</b> {excursion.date.strftime('%d %B')}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<b>Клиент:</b> {booking.last_name} {booking.first_name}\n"
            f"<b>Телефон:</b> {booking.phone_number}\n"
            f"<b>Кол-во гостей:</b> {booking.total_people}\n"
            f"<b>Сумма:</b> {excursion.price * booking.total_people} руб.\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<b>Статус:</b> {'🟢 Активна' if booking.is_active else '🔴 В обработке'}"
        )

        if not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=self._get_keyboard(booking.is_active, booking.id),
            )
        except Exception as e:
            logger.exception("Can not send message: {}", e)
            return False

        return True

    async def toggle_status(self, callback: CallbackQuery, booking_id: int) -> None:
        logger.debug(
            (
                "Toggle booking status with callback={callback!r}"
                "and booking_id={booking_id!r}"
            ),
            callback=callback,
            booking_id=booking_id,
        )
        if "🟢 Активна" in callback.message.text:  # type: ignore
            message = callback.message.text.replace("🟢 Активна", "🔴 В обработке")  # type: ignore
            is_active = False
        elif "🔴 В обработке" in callback.message.text:  # type: ignore
            message = callback.message.text.replace("🔴 В обработке", "🟢 Активна")  # type: ignore
            is_active = True
        else:
            message = callback.message.text  # type: ignore
            is_active = True

        await callback.message.edit_text(  # type: ignore
            message,
            parse_mode="HTML",
            reply_markup=self._get_keyboard(is_active, booking_id),
        )

    async def close(self) -> None:
        """Закрывает сессию бота"""
        if self.bot:
            await self.bot.session.close()


telegram_service = TelegramService()
