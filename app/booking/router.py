from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.depends import require_superuser
from app.auth.schemas import UserSchema
from app.booking.depends import get_booking_service
from app.booking.schemas import BookingCreate, BookingSchema
from app.booking.service import BookingService

booking_router = APIRouter(tags=["Booking"])


@booking_router.post("/booking")
async def create_booking(
    booking: BookingCreate,
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingSchema:
    new_booking = await service.create_booking(booking=booking)
    if new_booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excursion not found",
        )
    return new_booking


@booking_router.get("/bookings")
async def get_all_bookings(
    excursion_id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[BookingSchema]:
    bookings = await service.get_all_active_bookings(excursion_id)
    return bookings


@booking_router.get("/booking/{id}/toggle")
async def booking_toggle(
    id: int,
    service: Annotated[BookingService, Depends(get_booking_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> BookingSchema:
    booking = await service.toggle_booking(booking_id=id)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    return booking
