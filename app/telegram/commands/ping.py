from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.telegram.filter import ChatFilter

ping_router = Router()


@ping_router.message(Command("ping"), ChatFilter(settings.telegram_chat_id))
async def ping(message: Message) -> None:
    await message.answer("pong")
