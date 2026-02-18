from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from app.booking.schemas import BookingSchema, BookingStatus


def get_keyboard(booking: BookingSchema, is_user: bool = False) -> InlineKeyboardMarkup:
    logger.debug(
        "Generate keyboard with status={} and booking_id={}",
        booking.status,
        booking.id,
    )
    builder = InlineKeyboardBuilder()
    match booking.status, is_user:
        case BookingStatus.PENDING, True:  # На обработке, для пользователя
            text = "✅ Подтвердить"
            callback = f"user_confirm_booking:{booking.id}"

        case BookingStatus.PENDING, False:  # На обработке, для админа
            text = "✅ Подтвердить"
            callback = f"admin_confirm_booking:{booking.id}"

        case BookingStatus.CONFIRMED, True:  # Подтверждена, для пользователя
            text = ""
            callback = "pass"

        case BookingStatus.CONFIRMED, False:  # Подтверждена, для админа
            text = "❌ Отменить"
            callback = f"admin_cancel_booking:{booking.id}"

        case BookingStatus.CANCELLED, True:  # Отменена, для пользователя
            text = "✅ Подтвердить"
            callback = f"user_confirm_booking:{booking.id}"

        case BookingStatus.CANCELLED, False:  # Отменена, для админа
            text = "✅ Подтвердить"
            callback = f"admin_confirm_booking:{booking.id}"

        case _:
            text = "✅ Подтвердить"
            callback = f"admin_confirm_booking:{booking.id}"

    builder.button(
        text=text,
        callback_data=callback,
    )
    builder.adjust(1)
    return builder.as_markup()
