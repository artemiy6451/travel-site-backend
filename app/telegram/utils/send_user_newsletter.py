from datetime import datetime

from aiogram import Bot
from loguru import logger

from app.booking.schemas import BookingSchema
from app.excursions.schemas import ExcursionScheme
from app.utils.template_loader import render_template


async def send_newsletter_payment_to_user(
    bot: Bot,
    excursion: ExcursionScheme,
    booking: BookingSchema,
) -> None:
    logger.debug(
        "Send newsletter payment to user={} with excursion={} and booking={}",
        booking.telegram_user_id,
        excursion,
        booking,
    )
    try:
        context = {
            "excursion": excursion.model_dump(),
            "booking": booking.model_dump(),
            "now": datetime.now(),
        }
        text = await render_template("notification/remainder.html", **context)
        await bot.send_message(chat_id=booking.telegram_user_id, text=text)  # type: ignore
    except Exception as e:
        logger.exception("Can not send message: {}", e)
        raise Exception("Can not send message") from e


async def send_newsletter_bus_to_user(
    bot: Bot,
    excursion: ExcursionScheme,
    booking: BookingSchema,
) -> None:
    logger.debug(
        "Send newsletter bus to user={} with excursion={} and booking={}",
        booking.telegram_user_id,
        excursion,
        booking,
    )
    try:
        context = {
            "excursion": excursion.model_dump(),
            "booking": booking.model_dump(),
            "now": datetime.now(),
        }
        text = await render_template("notification/bus.html", **context)
        await bot.send_message(chat_id=booking.telegram_user_id, text=text)  # type: ignore
    except Exception as e:
        logger.exception("Can not send message: {}", e)
        raise Exception("Can not send message") from e
