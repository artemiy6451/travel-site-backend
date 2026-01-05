from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.booking.service import BookingService
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcurionService
from app.telegram.filter import ChatFilter
from app.template_loader import render_template

get_bookings_router = Router()


@get_bookings_router.message(
    Command("get_bookings"), ChatFilter(settings.telegram_chat_id)
)
async def choose_excursion(message: Message) -> None:
    await message.delete()
    excurison_service = ExcurionService()
    excursions = await excurison_service.get_active_excursions()

    keyboard = build_keyborad(excursions)

    text = render_template("get_bookings/hello.html")

    await message.answer(text, reply_markup=keyboard)


def build_keyborad(excursions: list[ExcursionScheme]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for excursion in excursions:
        builder.button(
            text=f"{excursion.title[:20]}...",
            callback_data=f"show_bookings_{excursion.id}",
        )

    builder.adjust(2, 2)
    return builder.as_markup()


@get_bookings_router.callback_query(F.data.startswith("show_bookings_"))
async def show_excursion_bookings(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        return

    excursion_id = int(callback.data.split("_")[2])

    excurison_service = ExcurionService()
    booking_service = BookingService()
    excursion = await excurison_service.get_excursion(excursion_id)
    bookings = await booking_service.get_all_bookings(excursion_id=excursion_id)

    total_people = 0
    total_sum = 0
    for booking in bookings:
        total_people += booking.total_people
        total_sum += booking.total_people * excursion.price

    context = {
        "excursion": excursion.model_dump(),
        "bookings": bookings,
        "total_people": total_people,
        "total_sum": total_sum,
    }

    text = render_template("get_bookings/bookings.html", **context)

    builder = InlineKeyboardBuilder()
    builder.button(text="Закрыть", callback_data="delete")

    await callback.message.edit_text(text, reply_markup=builder.as_markup())  # type: ignore


@get_bookings_router.callback_query(F.data.contains("delete"))
async def delete_message(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    await callback.message.delete()  # type: ignore
