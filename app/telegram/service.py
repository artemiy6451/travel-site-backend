from typing import List, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.template_loader import render_template


class TelegramNotificationService:
    def __init__(self) -> None:
        self.bot: Optional[Bot] = None
        self.notification_chat_ids: List[int] = []
        self._initialize_bot()

    def _initialize_bot(self) -> None:
        self.bot = Bot(
            token=settings.telegram_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

    def _get_keyboard(self, booking: BookingSchema) -> InlineKeyboardMarkup:
        logger.debug(
            "Generate keyboard with is_active={} and booking_id={}",
            booking.is_active,
            booking.id,
        )
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"{'❌ Отменить' if booking.is_active else '✅ Подтвердить'}",
            callback_data=f"toggle_booking:{booking.id}",
        )
        builder.adjust(1)
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

        context = {
            "booking": booking.model_dump(),
            "excursion": excursion.model_dump(),
            "formated_date": excursion.date.strftime("%d %B"),
            "sum": booking.total_people * excursion.price,
        }
        logger.debug(
            "Generate context with len: {} and context: {}", len(context), context
        )

        text = render_template("booking.html", **context)

        if not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=self._get_keyboard(booking),
            )
        except Exception as e:
            logger.exception("Can not send message: {}", e)
            return False

        return True

    async def toggle_status(
        self,
        callback: CallbackQuery,
        booking: BookingSchema,
        excursion: ExcursionScheme,
    ) -> None:
        logger.debug(
            (
                "Toggle booking status with callback={callback!r}"
                "and booking_id={booking_id!r}"
            ),
            callback=callback,
            booking_id=booking.id,
        )

        if callback.message is None:
            logger.warning(
                (
                    "Can not find message for booking={!r},"
                    "excursion={!r} and callback={!r}"
                ),
                booking,
                excursion,
                callback,
            )
            return

        context = self.generate_context(booking=booking, excursion=excursion)
        text = render_template("booking.html", **context)

        await callback.message.edit_text(  # type: ignore
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=self._get_keyboard(booking),
        )

    async def close(self) -> None:
        """Закрывает сессию бота"""
        if self.bot:
            await self.bot.session.close()

    @staticmethod
    def generate_context(booking: BookingSchema, excursion: ExcursionScheme) -> dict:
        context = {
            "booking": booking.model_dump(),
            "excursion": excursion.model_dump(),
            "formated_date": excursion.date.strftime("%d %B"),
            "sum": booking.total_people * excursion.price,
        }
        return context


telegram_service = TelegramNotificationService()
