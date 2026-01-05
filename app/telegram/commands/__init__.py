from app.telegram.commands.get_bookings import get_bookings_router
from app.telegram.commands.ping import ping_router
from app.telegram.commands.start import start_router
from app.telegram.commands.toggle_booking import toggle_booking_router

routers = [
    start_router,
    ping_router,
    toggle_booking_router,
    get_bookings_router,
]
