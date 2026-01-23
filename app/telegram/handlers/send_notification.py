from aiogram import Bot
from aiogram.enums import ParseMode
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.telegram.utils import get_keyboard
from app.template_loader import render_template


async def send_booking(
    bot: Bot,
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
        "formated_created_at": booking.created_at.strftime("%d %B %H:%m"),
        "sum": booking.total_people * excursion.price,
    }
    logger.debug("Generate context with len: {} and context: {}", len(context), context)

    text = render_template("booking.html", **context)

    try:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_keyboard(booking),
        )
    except Exception as e:
        logger.exception("Can not send message: {}", e)
        raise Exception("Can not send message") from e

    return True


async def send_error(bot: Bot, error_msg: str) -> None:
    logger.debug("Send notification with error_msg={}", error_msg)
    try:
        await bot.send_message(
            chat_id=settings.telegram_admin_id,
            text=error_msg,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.exception("Can not send message: {}", e)
        raise Exception("Can not send message") from e
