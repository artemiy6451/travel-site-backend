from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user is None or message.from_user.full_name is None:
        await message.answer(f"Hello, chat id: {message.chat.id}!")
    else:
        await message.answer(
            f"Hello, {html.bold(message.from_user.full_name)},"
            f"chat id: {message.chat.id}!"
        )
