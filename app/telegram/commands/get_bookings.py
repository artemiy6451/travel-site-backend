from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from faststream.rabbit import RabbitBroker

from app.booking.service import BookingService
from app.config import settings
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcursionService
from app.telegram.filter import ChatFilter
from app.utils.notifications import Notifications
from app.utils.template_loader import render_template

get_bookings_router = Router()


@get_bookings_router.message(
    Command("get_bookings"), ChatFilter(settings.telegram_chat_id)
)
async def choose_excursion(message: Message) -> None:
    await message.delete()
    excurison_service = ExcursionService()
    excursions = await excurison_service.get_active_excursions()

    keyboard = build_keyborad(excursions)

    text = await render_template("get_bookings/hello.html")

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

    excurison_service = ExcursionService()
    booking_service = BookingService()
    excursion = await excurison_service.get_excursion(excursion_id)
    bookings = await booking_service.get_all_confirmed_bookings_for_excursion(
        excursion_id=excursion_id
    )

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

    text = await render_template("get_bookings/bookings.html", **context)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Отправить рассылку",
        callback_data=f"send_newsletter_payment_{excursion.id}",
    )
    builder.button(
        text="Отправить номер автобуса",
        callback_data=f"send_newsletter_bus_{excursion.id}",
    )
    builder.button(text="Закрыть", callback_data="delete")
    builder.adjust(2, 2)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())  # type: ignore


@get_bookings_router.callback_query(F.data.contains("send_newsletter_payment_"))
async def send_payment_newsletter(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        return

    if callback.bot is None:
        return

    excursion_id = int(callback.data.split("_")[3])
    booking_service = BookingService()
    excursion_service = ExcursionService()
    all_bookings = await booking_service.get_all_confirmed_bookings_for_excursion(
        excursion_id=excursion_id
    )
    bookings = await booking_service.get_bookings_with_telegram_active(excursion_id)
    excursion = await excursion_service.get_excursion(excursion_id)

    if bookings is None:
        return

    sended_bookings = []

    for booking in bookings:
        if booking.telegram_user_id is None:
            continue
        async with Notifications(
            broker=RabbitBroker(), queue="newsletter_payment"
        ) as ns:
            await ns.send_to_rabbit(
                [booking.model_dump_json(), excursion.model_dump_json()]
            )
            sended_bookings.append(booking)

    need_to_send_bookings = [
        booking for booking in all_bookings if booking not in sended_bookings
    ]
    text = await render_template(
        "notification/sended_bookings.html",
        bookings=sended_bookings,
        need_to_send_bookings=need_to_send_bookings,
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="Закрыть", callback_data="delete")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())  # type: ignore


@get_bookings_router.callback_query(F.data.contains("send_newsletter_bus_"))
async def send_bus_newsletter(callback: CallbackQuery) -> None:
    if callback.message is None or callback.data is None:
        return

    if callback.bot is None:
        return

    excursion_id = int(callback.data.split("_")[3])
    booking_service = BookingService()
    excursion_service = ExcursionService()
    all_bookings = await booking_service.get_all_confirmed_bookings_for_excursion(
        excursion_id=excursion_id
    )
    bookings = await booking_service.get_bookings_with_telegram_active(excursion_id)
    excursion = await excursion_service.get_excursion(excursion_id)

    if bookings is None:
        return

    if excursion.bus_number == 0:
        await callback.answer(
            "Номер автобуса не указан, сначала укажите его на сайте",
            show_alert=True,
        )
        return

    sended_bookings = []

    for booking in bookings:
        if booking.telegram_user_id is None:
            continue
        async with Notifications(broker=RabbitBroker(), queue="newsletter_bus") as ns:
            await ns.send_to_rabbit(
                [
                    booking.model_dump_json(),
                    excursion.model_dump_json(),
                ]
            )
            sended_bookings.append(booking)

    need_to_send_bookings = [
        booking for booking in all_bookings if booking not in sended_bookings
    ]
    text = await render_template(
        "notification/sended_bookings.html",
        bookings=sended_bookings,
        need_to_send_bookings=need_to_send_bookings,
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="Закрыть", callback_data="delete")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())  # type: ignore


@get_bookings_router.callback_query(F.data.contains("delete"))
async def delete_message(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    await callback.message.delete()  # type: ignore
