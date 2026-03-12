import asyncio
import locale

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.telegram.utils.send_notification import send_booking, send_error
from app.telegram.utils.send_user_newsletter import (
    send_newsletter_bus_to_user,
    send_newsletter_payment_to_user,
)
from app.utils.logging import setup_new_logger
from app.utils.rabbitmq import rabbit_broker

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
setup_new_logger()

bot = Bot(
    token=settings.telegram_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


@rabbit_broker.subscriber("bookings")
async def handle_send_booking(data: list[str]) -> None:
    try:
        logger.debug("Recieve from rabbit: {}", data)
        booking = BookingSchema.model_validate_json(data[0])
        excursion = ExcursionScheme.model_validate_json(data[1])

        logger.debug("Booking parsed data: {}", booking)
        logger.debug("Excursion parsed data: {}", excursion)

        await send_booking(bot=bot, booking=booking, excursion=excursion)

    except Exception as e:
        logger.exception("Error while send booking notification: {}", e)
        await asyncio.sleep(60)
        await handle_send_booking(data)


@rabbit_broker.subscriber("newsletter_payment")
async def handle_newsletter_payment(data: list[str]) -> None:
    try:
        logger.debug("Recieve from rabbit: {}", data)
        booking = BookingSchema.model_validate_json(data[0])
        excursion = ExcursionScheme.model_validate_json(data[1])

        logger.debug("Booking parsed data: {}", booking)
        logger.debug("Excursion parsed data: {}", excursion)

        await send_newsletter_payment_to_user(
            bot=bot, excursion=excursion, booking=booking
        )
    except Exception as e:
        logger.exception("Error while send newsletter: {}", e)
        await asyncio.sleep(60)
        await handle_newsletter_payment(data)


@rabbit_broker.subscriber("newsletter_bus")
async def handle_newsletter_bus(data: list[str]) -> None:
    try:
        logger.debug("Recieve from rabbit: {}", data)
        booking = BookingSchema.model_validate_json(data[0])
        excursion = ExcursionScheme.model_validate_json(data[1])

        logger.debug("Booking parsed data: {}", booking)
        logger.debug("Excursion parsed data: {}", excursion)

        await send_newsletter_bus_to_user(bot=bot, excursion=excursion, booking=booking)
    except Exception as e:
        logger.exception("Error while send newsletter: {}", e)
        await asyncio.sleep(60)
        await handle_newsletter_bus(data)


@rabbit_broker.subscriber("errors")
async def handle_send_error(data: list[str]) -> None:
    try:
        logger.debug("Recieve from rabbit: {}", data)
        error_msg = data[0]

        logger.debug("Error parsed data: {}", error_msg)

        await send_error(bot=bot, error_msg=error_msg)
    except Exception:
        await asyncio.sleep(60)
        await handle_send_error(data)
