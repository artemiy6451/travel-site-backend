from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app.booking.schemas import BookingSchema, BookingStatus
from app.excursions.schemas import ExcursionScheme


def get_keyboard(booking: BookingSchema, is_user: bool = False) -> InlineKeyboardMarkup:
    logger.debug(
        "Generate keyboard with status={} and booking_id={}",
        booking.status,
        booking.id,
    )
    builder = InlineKeyboardBuilder()
    builder.button(
        text=(
            "❌ Отменить"
            if not is_user
            else "" if booking.status == BookingStatus.CONFIRMED else "✅ Подтвердить"
        ),
        callback_data=("user_" if is_user else "") + f"toggle_booking:{booking.id}",
    )
    builder.adjust(1)
    return builder.as_markup()


def generate_context(booking: BookingSchema, excursion: ExcursionScheme) -> dict:
    context = {
        "booking": booking.model_dump(),
        "excursion": excursion.model_dump(),
        "formated_date": excursion.date.strftime("%d %B"),
        "sum": booking.total_people * excursion.price,
    }
    return context
