"""File with booking service."""

import asyncio
from typing import Any

from loguru import logger

from app.booking.exceptions import BookingNotFoundError
from app.booking.models import BookingModel
from app.booking.schemas import BookingCreate, BookingSchema, BookingStatus
from app.booking.utils import change_bookings_status
from app.database import async_session_maker
from app.excursions.schemas import ExcursionScheme
from app.excursions.service import ExcursionService
from app.repository import SQLAlchemyRepository
from app.user.schemas import UserSchema
from app.utils.notifications import Notifications
from app.utils.rabbitmq import rabbit_broker


class BookingService:
    """Service for booking models."""

    def __init__(self) -> None:
        """Create `booking` and `excursion` service."""
        self.booking_repository: SQLAlchemyRepository[BookingModel] = (
            SQLAlchemyRepository(async_session_maker, BookingModel)
        )
        self.excursion_service: ExcursionService = ExcursionService()

    async def get_booking(self, booking_id: int) -> BookingSchema:
        """Get booking by id.

        Args:
            booking_id: `int`

        Return: `BookingSchema`

        Raise: `BookingNotFoundError` if booking does not exist
        """
        booking = await self.booking_repository.find_one(
            filter=BookingModel.id == booking_id
        )
        if booking is None:
            raise BookingNotFoundError()

        return booking.to_read_model()

    async def create_booking(self, booking: BookingCreate) -> BookingSchema:
        """Create a new booking.

        Args:
            booking: `BookingCreate`

        Return:
        `BookingSchema`
        """
        excursion = await self.excursion_service.get_excursion(booking.excursion_id)

        new_booking = await self.booking_repository.add_one(booking.model_dump())
        formated_booking = new_booking.to_read_model()

        asyncio.create_task(
            self._send_booking_notification(
                booking=formated_booking, excursion=excursion
            )
        )
        return formated_booking

    async def get_all_confirmed_bookings_for_excursion(
        self, excursion_id: int
    ) -> list[BookingSchema]:
        """Get all bookings with status CONFIRMED for one excursion.

        Args:
            excursion_id: `int`

        Return: `list[BookingSchema]`
        """
        filter_by = (BookingModel.status == BookingStatus.CONFIRMED) & (
            BookingModel.excursion_id == excursion_id
        )
        bookings = await self.booking_repository.find_all(
            filter_by=filter_by,
            order_by=BookingModel.created_at,
        )
        return [booking.to_read_model() for booking in bookings]

    async def get_user_bookings(self, user: UserSchema) -> list[BookingSchema]:
        filter_by = BookingModel.phone_number == user.phone_number

        bookings = await self.booking_repository.find_all(
            filter_by=filter_by,
            order_by=BookingModel.created_at,
        )
        return [booking.to_read_model() for booking in bookings]

    async def toggle_booking_status(
        self,
        booking_id: int,
    ) -> BookingSchema:
        """Toggle booking status.

        Args:
            booking_id: `int`

        Return: `BookingSchema`

        Raise: `BookingNotFoundError` if booking does not exist
        """
        booking = await self.get_booking(booking_id=booking_id)

        excursion = await self.excursion_service.get_excursion(booking.excursion_id)

        new_status = change_bookings_status(booking)

        data: dict[str, Any] = {"status": new_status}

        new_booking = await self.booking_repository.update(
            where=BookingModel.id == booking_id,
            data=data,
        )
        if new_booking is None:
            raise BookingNotFoundError()

        formated_booking = new_booking.to_read_model()

        await self._change_people_left_by_booking_status(
            booking=formated_booking,
            excursion=excursion,
        )

        return formated_booking

    async def deactivate_past_bookings(self) -> None:
        """Deactivate past bookings.

        Deactivate all bookings with status CANCELLED or CONFIRMED.

        Return: `None`
        """
        logger.info("Deactivate past bookings")
        excursions = await self.excursion_service.get_excursions_with_expired_date()
        logger.debug("Found {} excursions to update.", len(excursions))

        for excursion in excursions:
            where = (BookingModel.excursion_id == excursion.id) & (
                (BookingModel.status == BookingStatus.CANCELLED)
                | (BookingModel.status == BookingStatus.CONFIRMED)
            )
            bookings = await self.booking_repository.update_all(
                where=where, data={"status": BookingStatus.EXPIRED}
            )
            logger.debug("Booking expired={}", len(bookings))

    async def _change_people_left_by_booking_status(
        self,
        booking: BookingSchema,
        excursion: ExcursionScheme,
    ) -> None:
        """Change people left by booking status.

        Args:
            booking: `BookingSchema`
            excursion: `ExcursionScheme`

        Return: `None`
        """
        if booking.status == BookingStatus.CONFIRMED:
            excursion = await self.excursion_service.change_people_left_count(
                excursion.id, booking.total_people
            )
        else:
            excursion = await self.excursion_service.change_people_left_count(
                excursion.id, -booking.total_people
            )

    async def _send_booking_notification(
        self,
        booking: BookingSchema,
        excursion: ExcursionScheme,
    ) -> None:
        """Send booking notification.

        Send booking notification to rabbitmq queue `bookings`.

        Args:
            booking: `BookingSchema`
            excursion: `ExcursionScheme`

        Return: `None`
        """
        async with Notifications(broker=rabbit_broker, queue="bookings") as ns:
            await ns.send_to_rabbit(
                [
                    booking.model_dump_json(),
                    excursion.model_dump_json(),
                ]
            )
