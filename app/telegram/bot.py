import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.booking.schemas import BookingSchema
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.logging import setup_new_logger
from app.rabbitmq import get_rabit_broker
from app.telegram.commands import routers
from app.telegram.handlers.send_notification import send_notification
from app.telegram.handlers.toggle_booking import toggle_booking_router

setup_new_logger()

bot = Bot(
    token=settings.telegram_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

rabit_broker = get_rabit_broker()


@rabit_broker.subscriber("bookings")
async def handle_send_notification(data: list[str]) -> None:
    try:
        logger.debug("Recieve from rabbit: {}", data)
        booking = BookingSchema.model_validate_json(data[0])
        excursion = ExcursionScheme.model_validate_json(data[1])

        logger.debug("Booking parsed data: {}", booking)
        logger.debug("Excursion parsed data: {}", excursion)

        await send_notification(bot=bot, booking=booking, excursion=excursion)
    except Exception:
        await asyncio.sleep(60)
        await handle_send_notification(data)


for router in routers:
    dp.include_router(router)

dp.include_router(toggle_booking_router)


async def main() -> None:
    async with rabit_broker:
        await rabit_broker.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
