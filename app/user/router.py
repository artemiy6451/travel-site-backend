from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.depends import get_current_user, get_user_service
from app.booking.schemas import BookingSchema
from app.user.schemas import UserSchema
from app.user.service import UserService

user_router = APIRouter(tags=["User"])


@user_router.get("/users/me", response_model=UserSchema)
def read_users_me(user: Annotated[UserSchema, Depends(get_current_user)]) -> UserSchema:
    """Get current user."""
    return user


@user_router.get("/users/get_bookings", response_model=list[BookingSchema])
async def get_user_bookings(
    user: Annotated[UserSchema, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[BookingSchema]:
    return await service.get_user_bookings(user)
