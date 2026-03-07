"""FastAPI router file for booking."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.depends import require_superuser
from app.auth.schemas import UserSchema
from app.booking.depends import get_booking_service
from app.booking.exceptions import BookingNotFoundError
from app.booking.schemas import BookingCreate, BookingSchema
from app.booking.service import BookingService

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
    "/bookings",
    response_model=list[BookingSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_bookings(
    excursion_id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[BookingSchema]:
    """Get all bookings with status CONFIRMED for one excursion."""
    bookings = await service.get_all_confirmed_bookings_for_excursion(excursion_id)
    return bookings


@booking_router.get(
    "/booking/{id}/toggle",
    response_model=BookingSchema,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"detail": "Booking not found"},
    },
)
async def booking_toggle(
    id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> BookingSchema:
    """Change booking status to `CANCELLED` or `CONFIRMED`."""
    try:
        booking = await service.toggle_booking_status(booking_id=id)
        return booking
    except BookingNotFoundError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail=err.message,
        ) from err
