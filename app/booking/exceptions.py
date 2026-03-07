"""Booking exceptions file."""

from fastapi import status

from app.exceptions import ServiceError


class BookingNotFoundError(ServiceError):
    """Booking not found error."""

    status_code: int = status.HTTP_404_NOT_FOUND
    message: str = "Booking not found"
