from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from app.booking.service import BookingService
from app.excursions.service import ExcurionService
from app.telegram.service import telegram_service

toggle_booking_router = Router()


@toggle_booking_router.callback_query(F.data.startswith("toggle_booking:"))
async def handle_toggle_booking(callback: CallbackQuery) -> None:
    logger.debug("Handle toggle booking with callback: {}", callback)

    try:
        booking_service = BookingService()
        excursion_service = ExcurionService()

        if callback.data is None or callback.message is None:
            raise Exception

        booking_id = int(callback.data.split(":")[1])
        booking = await booking_service.get_booking(booking_id)
        if booking is None:
            await callback.answer("Бронь не найдена!", show_alert=True)
            return

        excursion = await excursion_service.get_excursion(booking.excursion_id)

        updated_booking = await booking_service.toggle_booking(booking.id)
        if updated_booking is None:
            await callback.answer("Бронь не найдена!", show_alert=True)
            return

        status = "✅ активирована" if updated_booking.is_active else "❌ отменена"

        await telegram_service.toggle_status(callback, updated_booking, excursion)

        message = f"Бронь #{booking_id} {status}!"
        await callback.answer(message)

        logger.debug("Booking toggled: {}", message)

    except Exception as e:
        logger.exception(f"Ошибка обработки toggle_booking: {e}")
        await callback.answer("Произошла ошибка!", show_alert=True)
