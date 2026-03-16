"""Auth service rewritten to use server-side session cookies instead of JWT."""

import uuid

from fastapi import HTTPException, status
from loguru import logger
from passlib.context import CryptContext

from app.config import settings
from app.user.schemas import UserSchema
from app.user.service import UserService
from app.utils.redis_config import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Auth service."""

    def __init__(self) -> None:
        self.user_service = UserService()
        self.session_ttl = settings.session_cookie_max_age

    async def authenticate_user(self, email: str, password: str) -> UserSchema:
        """Authenticate user and return schema on success."""
        logger.debug(
            "Authenticate user with email={}",
            email,
        )
        user = await self.user_service.get_user_by_email(email=email)
        if not user:
            logger.debug("User not found: {}", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not self.verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            logger.debug("Password mismatch for {}", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        return user.to_read_model()

    def create_session(self, user: UserSchema) -> str:
        """Create server-side session and return session id."""
        session_id = uuid.uuid4().hex
        redis_payload = {
            "email": user.email,
            "is_superuser": str(user.is_superuser),
        }
        # Store session in Redis with TTL
        redis_client.hset(session_id, mapping=redis_payload)
        redis_client.expire(session_id, self.session_ttl)
        logger.debug("Created session {} for user {}", session_id, user.email)
        return session_id

    def destroy_session(self, session_id: str) -> None:
        """Invalidate session."""
        redis_client.delete(session_id)
        logger.debug("Destroyed session {}", session_id)

    async def get_user_by_session(self, session_id: str) -> UserSchema:
        """Validate session and return user schema."""
        payload = redis_client.hgetall(session_id)
        if not payload:
            logger.warning("Session not found or expired: {}", session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        email = payload.get("email")  # type: ignore
        is_superuser = payload.get("is_superuser", "False") == "True"  # type: ignore
        user = await self.user_service.get_user_by_email(email=email)  # type: ignore
        if not user:
            logger.warning("User from session not found: {}", email)
            self.destroy_session(session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        user_schema = user.to_read_model()
        user_schema.is_superuser = is_superuser
        return user_schema

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Get password hash."""
        return pwd_context.hash(password)
