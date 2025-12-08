import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.booking.service import BookingService
from app.telegram.service import telegram_service

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("toggle_booking:"))
async def handle_toggle_booking(callback: CallbackQuery) -> None:
    try:
        booking_service = BookingService()

        if callback.data is None or callback.message is None:
            raise Exception

        booking_id = int(callback.data.split(":")[1])

        updated_booking = await booking_service.toggle_booking(booking_id)
        if updated_booking is None:
            await callback.answer("Бронь не найдена!", show_alert=True)
            return

        status = "✅ активирована" if updated_booking.is_active else "❌ отменена"

        await telegram_service.toggle_status(callback, booking_id)
        await callback.answer(f"Бронь #{booking_id} {status}!")

    except Exception as e:
        logger.error(f"Ошибка обработки toggle_booking: {e}")
        await callback.answer("Произошла ошибка!", show_alert=True)
