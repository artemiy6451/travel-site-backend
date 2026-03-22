"""FastAPI router file for booking."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.depends import get_current_user, require_superuser
from app.booking.depends import get_booking_service
from app.booking.exceptions import (
    BookingAlreadyCancelledError,
    BookingAlreadyConfirmedError,
    BookingNotFoundError,
)
from app.booking.schemas import BookingCreate, BookingSchema
from app.booking.service import BookingService
from app.user.schemas import UserSchema

booking_router = APIRouter(tags=["Booking"])


@booking_router.post(
    "/booking",
    response_model=BookingSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    booking: BookingCreate,
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingSchema:
    """Create a new booking."""
    new_booking = await service.create_booking(booking=booking)
    return new_booking


@booking_router.get(
    "/booking/excursion/{excursion_id}",
    response_model=list[BookingSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_bookings_for_excursions(
    excursion_id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[BookingSchema]:
    """Get all bookings with status CONFIRMED for one excursion."""
    bookings = await service.get_all_bookings_for_excursion(excursion_id)
    return bookings


@booking_router.post(
    "/booking/{booking_id}/confirm",
    response_model=BookingSchema,
    status_code=status.HTTP_200_OK,
)
async def confirm_booking(
    booking_id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(get_current_user)],
) -> BookingSchema:
    try:
        return await service.confrim_booking(booking_id)
    except (
        BookingNotFoundError,
        BookingAlreadyConfirmedError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@booking_router.post(
    "/booking/{booking_id}/cancel",
    response_model=BookingSchema,
    status_code=status.HTTP_200_OK,
)
async def cancel_booking(
    booking_id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(get_current_user)],
) -> BookingSchema:
    try:
        return await service.cancel_booking(booking_id)
    except (
        BookingNotFoundError,
        BookingAlreadyCancelledError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
