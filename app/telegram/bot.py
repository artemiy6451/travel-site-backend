import asyncio

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config import settings
from app.logging.utils import remove_all_logers, setup_new_logger
from app.telegram.filter import ChatFilter
from app.telegram.handlers import router

bot = Bot(
    token=settings.telegram_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

dp.include_router(router)

remove_all_logers()

setup_new_logger()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}, chat id: {message.chat.id}!"  # type: ignore
    )


@dp.message(Command("ping"), ChatFilter(settings.telegram_chat_id))
async def ping(message: Message) -> None:
    await message.answer("pong")


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
