from app.booking.service import BookingService


def get_booking_service() -> BookingService:
    return BookingService()
