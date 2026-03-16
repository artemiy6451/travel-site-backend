"""Auth dependencies using cookie-based sessions."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from loguru import logger

from app.auth.service import AuthService, UserService
from app.user.schemas import UserSchema


async def get_user_service() -> UserService:
    """Get user service."""
    logger.debug("Get user service")
    return UserService()


async def get_auth_service() -> AuthService:
    """Get auth service."""
    logger.debug("Get auth service")
    return AuthService()


async def get_current_user(
    session_id: Annotated[str | None, Cookie(alias="session_id")],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserSchema:
    """Return current user from session cookie."""
    if not session_id:
        logger.warning("Missing session cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = await service.get_user_by_session(session_id)
    return user


def require_superuser(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> UserSchema:
    """Require superuser."""
    if not current_user.is_superuser:
        logger.warning("Admin privileges required!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user
