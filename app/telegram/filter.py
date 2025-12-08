from aiogram import types
from aiogram.filters import Filter


class ChatFilter(Filter):
    def __init__(self, allowed_chat_id: int):
        self.allowed_chat_id = allowed_chat_id

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == self.allowed_chat_id
