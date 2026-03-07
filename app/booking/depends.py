"""File with booking dependencies."""

from app.booking.service import BookingService


def get_booking_service() -> BookingService:
    """Get booking service."""
    return BookingService()
