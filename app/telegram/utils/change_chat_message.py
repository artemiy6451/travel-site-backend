from datetime import datetime

from aiogram.enums import ParseMode
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.telegram.bot import bot
from app.telegram.utils.keyboard import get_keyboard
from app.telegram.utils.retry import retry
from app.template_loader import render_template


@retry(max_attempts=10, delay=60)
async def change_chat_message(
    booking: BookingSchema, excursion: ExcursionScheme
) -> None:
    logger.debug("Change chat message for booking: {}", booking)

    context = {
        "booking": booking.model_dump(),
        "excursion": excursion.model_dump(),
        "formated_date": excursion.date.strftime("%d %B"),
        "formated_created_at": booking.created_at.strftime("%d %B %H:%M"),
        "formated_changed_at": booking.changed_at.strftime("%d %B %H:%M"),
        "sum": booking.total_people * excursion.price,
    }
    logger.debug("Generate context with len: {} and context: {}", len(context), context)

    text = await render_template("booking.html", **context)
    await bot.edit_message_text(
        text=text,
        chat_id=settings.telegram_chat_id,
        message_id=booking.telegram_message_id,
        reply_markup=get_keyboard(booking),
    )


@retry(max_attempts=10, delay=15)
async def send_notification_to_user(
    booking: BookingSchema, excursion: ExcursionScheme
) -> bool:
    if booking.telegram_user_id is None:
        return False

    context = {
        "booking": booking.model_dump(),
        "excursion": excursion.model_dump(),
        "sum": booking.total_people * excursion.price,
        "now": datetime.now(),
    }
    logger.debug("Generate context with len: {} and context: {}", len(context), context)

    text = await render_template("user/confirm_booking.html", **context)

    await bot.send_message(
        text=text,
        chat_id=booking.telegram_user_id,
        reply_markup=get_keyboard(booking, is_user=True),
        parse_mode=ParseMode.HTML,
    )
    return True
