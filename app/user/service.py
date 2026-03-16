from fastapi import HTTPException, status
from loguru import logger
from passlib.context import CryptContext

from app.database import async_session_maker
from app.repository import SQLAlchemyRepository
from app.user.models import UserModel
from app.user.schemas import UserCreate, UserSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self) -> None:
        """Create user repository."""
        self.repository: SQLAlchemyRepository[UserModel] = SQLAlchemyRepository(
            async_session_maker, UserModel
        )
        logger.debug("Setup UserService with repository: {}", self.repository)

    async def get_user_by_email(self, email: str) -> UserModel | None:
        """Get user by email.

        Args:
            email: `str`

        Return: `UserModel | None`
        """
        logger.debug("Find user by email: {}", email)
        filter = UserModel.email == email
        user = await self.repository.find_one(filter=filter)
        logger.debug("Returning user: {!r}", user)
        return user if user else None

    async def create_user(self, user: UserCreate) -> UserSchema:
        """Create user.

        Args:
            user: `UserCreate`

        Return: `UserSchema`
        """
        logger.debug("Create user with data: {!r}", user)

        exist_user = await self.get_user_by_email(user.email)
        if exist_user:
            logger.warning("User with email {!r} already exist", {exist_user.email})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        userdata = {
            "email": user.email,
            "hashed_password": self.get_password_hash(user.password),
        }
        created_user = await self.repository.add_one(userdata)
        logger.debug("User crated: {!r}", created_user)
        return created_user.to_read_model()

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
