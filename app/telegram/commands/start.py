from datetime import datetime

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.booking.service import BookingService
from app.excursions.service import ExcursionService
from app.telegram.utils.keyboard import get_keyboard
from app.template_loader import render_template

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.text is None:
        return

    command_args = message.text.split()

    if len(command_args) > 1 and command_args[1].startswith("confirm_"):
        booking_id = int(command_args[1].replace("confirm_", ""))

        booking_service = BookingService()
        excursion_service = ExcursionService()

        booking = await booking_service.get_booking(booking_id)

        if booking is None or booking.excursion_id is None:
            await message.answer("👋 Привет! Не могу найти нужного бронированния")
            return

        excursion = await excursion_service.get_excursion(booking.excursion_id)

        context = {
            "booking": booking.model_dump(),
            "excursion": excursion.model_dump(),
            "sum": booking.total_people * excursion.price,
            "now": datetime.now(),
        }

        text = await render_template("user/confirm_booking.html", **context)

        await message.answer(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_keyboard(booking, is_user=True),
        )

        booking_service = BookingService()
        await booking_service.save_telegram_user_chat_id(booking.id, message.chat.id)

    else:
        await message.answer(
            "👋 Привет! Я только подтверждаю бронирования и рассылаю важные сообщения."
            "\n\nЕсли у Вас вознилки какие-то проблеммы с бронированием "
            "или повились вопросы, Вы можете написать нам в телеграмме:\n"
            "Виталий - +7(978)700-58-59\n"
            "Артём - @l0kach"
        )
