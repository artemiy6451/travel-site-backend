import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.logging import setup_new_logger
from app.rabbitmq import rabbit_broker
from app.telegram.commands import routers
from app.telegram.handlers.send_notification import send_booking, send_error
from app.telegram.handlers.toggle_booking import toggle_booking_router

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
    except Exception:
        await asyncio.sleep(60)
        await handle_send_booking(data)


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


for router in routers:
    dp.include_router(router)

dp.include_router(toggle_booking_router)


async def main() -> None:
    async with rabbit_broker:
        await rabbit_broker.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
