import asyncio

from app.rabbitmq import rabbit_broker
from app.telegram.bot import bot, dp
from app.telegram.commands import routers
from app.telegram.handlers.toggle_booking import toggle_booking_router

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
