"""Auth router."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.auth.depends import get_auth_service, get_user_service
from app.auth.service import AuthService, UserService
from app.config import settings
from app.user.schemas import UserCreate, UserLogin, UserSchema

auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/register", response_model=UserSchema)
async def register(
    user: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
) -> UserSchema:
    """Register new user."""
    created_user = await service.create_user(user)
    return created_user


@auth_router.post("/login", response_model=UserSchema)
async def login(
    user: UserLogin,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserSchema:
    """Login user, set session cookie, and return user info."""
    authenticated_user = await auth_service.authenticate_user(user.email, user.password)
    session_id = auth_service.create_session(authenticated_user)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=auth_service.session_ttl,
    )
    return authenticated_user


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie(alias="session_id")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Logout user: drop server session and clear cookie."""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    auth_service.destroy_session(session_id)
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
