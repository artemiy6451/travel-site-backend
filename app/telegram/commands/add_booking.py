from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.telegram.filter import ChatFilter

add_booking_router = Router()


@add_booking_router.message(Command("add"), ChatFilter(settings.telegram_chat_id))
async def add_booking(message: Message) -> None:
    pass
