from app.telegram.commands.get_bookings import get_bookings_router
from app.telegram.commands.start import start_router

routers = [
    start_router,
    get_bookings_router,
]
