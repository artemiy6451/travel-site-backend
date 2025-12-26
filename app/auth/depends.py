from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from loguru import logger

from app.auth.schemas import UserSchema
from app.auth.service import ALGORITHM, UserService
from app.config import settings

security = HTTPBearer()


async def get_user_service() -> UserService:
    logger.debug("Get user service")
    return UserService()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            logger.warning("Can not validate user credentials!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from JWTError

        is_superuser: bool = payload.get("is_superuser", False)
        logger.debug("Found email: {}, is user admin: {}", email, is_superuser)

    except JWTError:
        logger.warning("Can not validate user credentials!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from JWTError

    user = await service.get_user_by_email(email=email)
    if user is None:
        logger.warning("Can not validate user credentials!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from JWTError

    user.is_superuser = is_superuser
    return user.to_read_model()


def require_superuser(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> UserSchema:
    if not current_user.is_superuser:
        logger.warning("Admin privileges required!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user
