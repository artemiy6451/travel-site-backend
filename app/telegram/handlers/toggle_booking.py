from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import CallbackQuery
from loguru import logger

from app.booking.schemas import BookingSchema, BookingStatus
from app.booking.service import BookingService
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcurionService
from app.telegram.utils import get_keyboard
from app.template_loader import render_template

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

        status = (
            "✅ активирована"
            if updated_booking.status == BookingStatus.CONFIRMED
            else "❌ отменена"
        )

        await toggle_status(callback, updated_booking, excursion)

        message = f"Бронь #{booking_id} {status}!"
        await callback.answer(message)

        logger.debug("Booking toggled: {}", message)

    except Exception as e:
        logger.exception(f"Ошибка обработки toggle_booking: {e}")
        await callback.answer("Произошла ошибка!", show_alert=True)


async def toggle_status(
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
            ("Can not find message for booking={!r},excursion={!r} and callback={!r}"),
            booking,
            excursion,
            callback,
        )
        return
    context = {
        "booking": booking.model_dump(),
        "excursion": excursion.model_dump(),
        "formated_date": excursion.date.strftime("%d %B"),
        "formated_created_at": booking.created_at.strftime("%d %B %H:%M"),
        "formated_changed_at": booking.changed_at.strftime("%d %B %H:%M"),
        "sum": booking.total_people * excursion.price,
    }
    text = render_template("booking.html", **context)

    await callback.message.edit_text(  # type: ignore
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_keyboard(booking),
    )
