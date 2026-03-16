from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.depends import get_current_user
from app.user.schemas import UserSchema

user_router = APIRouter(tags=["User"])


@user_router.get("/users/me", response_model=UserSchema)
def read_users_me(user: Annotated[UserSchema, Depends(get_current_user)]) -> UserSchema:
    """Get current user."""
    return user
