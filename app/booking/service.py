import asyncio

from fastapi import HTTPException

from app.booking.models import BookingModel
from app.booking.schemas import BookingCreate, BookingSchema, BookingStatus
from app.database import async_session_maker
from app.excursions.models import ExcursionModel
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcurionService
from app.notifications import Notifications
from app.rabbitmq import rabbit_broker
from app.repository import SQLAlchemyRepository


class BookingService:
    def __init__(self) -> None:
        self.booking_repository: SQLAlchemyRepository[BookingModel] = (
            SQLAlchemyRepository(async_session_maker, BookingModel)
        )
        self.excursion_repository: SQLAlchemyRepository[ExcursionModel] = (
            SQLAlchemyRepository(async_session_maker, ExcursionModel)
        )
        self.excursion_service: ExcurionService = ExcurionService()

    async def create_booking(self, booking: BookingCreate) -> BookingSchema | None:
        get_excursion = await self.excursion_repository.find_one(
            ExcursionModel.id == booking.excursion_id
        )
        if get_excursion is None:
            return None

        excursion = get_excursion.to_read_model()

        new_booking = await self.booking_repository.add_one(booking.model_dump())
        formated_booking = new_booking.to_read_model()

        asyncio.create_task(
            self._send_booking_notification(
                booking=formated_booking, excursion=excursion
            )
        )
        return formated_booking

    async def get_all_active_bookings(self, excursion_id: int) -> list[BookingSchema]:
        join_by = ExcursionModel
        filter_by = (ExcursionModel.id == excursion_id) & (
            BookingModel.status == BookingStatus.CONFIRMED
        )
        bookings = await self.booking_repository.find_all(
            join_by=join_by, filter_by=filter_by, order_by=BookingModel.created_at
        )
        return [booking.to_read_model() for booking in bookings]

    async def get_booking(self, booking_id: int) -> BookingSchema | None:
        booking = await self.booking_repository.find_one(
            filter=BookingModel.id == booking_id
        )
        if booking is None:
            return None

        return booking.to_read_model()

    async def toggle_booking(self, booking_id: int) -> BookingSchema | None:
        booking = await self.get_booking(booking_id=booking_id)
        if booking is None:
            return None

        get_excursion = await self.excursion_repository.find_one(
            ExcursionModel.id == booking.excursion_id
        )
        if get_excursion is None:
            return None

        match booking.status:
            case BookingStatus.PENDING:
                new_status = BookingStatus.CONFIRMED
            case BookingStatus.CONFIRMED:
                new_status = BookingStatus.CANCELLED
            case BookingStatus.CANCELLED:
                new_status = BookingStatus.CONFIRMED
            case _:
                new_status = BookingStatus.PENDING

        where = BookingModel.id == booking_id
        new_booking = await self.booking_repository.update(
            where=where,
            data={"status": new_status},
        )
        if new_booking is None:
            raise HTTPException(
                status_code=404,
                detail="Can not find booking.",
            )

        formated_booking = new_booking.to_read_model()

        if formated_booking.status == BookingStatus.CONFIRMED:
            await self.excursion_service.change_people_left(
                get_excursion.id, formated_booking.total_people
            )
        else:
            await self.excursion_service.change_people_left(
                get_excursion.id, -formated_booking.total_people
            )

        return formated_booking

    async def _send_booking_notification(
        self, booking: BookingSchema, excursion: ExcursionScheme
    ) -> None:
        async with Notifications(broker=rabbit_broker, queue="bookings") as ns:
            await ns.send_to_rabbit(
                [
                    booking.model_dump_json(),
                    excursion.model_dump_json(),
                ]
            )
