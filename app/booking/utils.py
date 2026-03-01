"""File with booking utils."""

from app.booking.schemas import BookingSchema, BookingStatus


def change_bookings_status(booking: BookingSchema) -> BookingStatus:
    """Change booking status to CONFIRMED or CANCELLED.

    Args:
        booking: `BookingSchema`

    Return: `BookingStatus`
    """
    match booking.status:
        case BookingStatus.PENDING:
            return BookingStatus.CONFIRMED
        case BookingStatus.CONFIRMED:
            return BookingStatus.CANCELLED
        case BookingStatus.CANCELLED:
            return BookingStatus.CONFIRMED
        case _:
            return BookingStatus.PENDING
