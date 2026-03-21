from fastapi import HTTPException, status
from loguru import logger
from passlib.context import CryptContext

from app.booking.schemas import BookingSchema
from app.booking.service import BookingService
from app.database import async_session_maker
from app.repository import SQLAlchemyRepository
from app.user.exceptions import UserNotFoundExceptionError
from app.user.models import UserModel
from app.user.schemas import UserCreate, UserSchema, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self) -> None:
        """Create user repository."""
        self.repository: SQLAlchemyRepository[UserModel] = SQLAlchemyRepository(
            async_session_maker, UserModel
        )
        self.booking_service: BookingService = BookingService()
        logger.debug("Setup UserService with repository: {}", self.repository)

    async def create_user(self, user: UserCreate) -> UserSchema:
        """Create user.

        Args:
            user: `UserCreate`

        Return: `UserSchema`
        """
        logger.debug("Create user with data: {}", user)

        try:
            exist_user = await self.get_user_by_email(user.email)
            if exist_user:
                logger.warning("User with email {} already exist", {exist_user.email})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
        except UserNotFoundExceptionError:
            pass

        userdata = {
            "email": user.email,
            "hashed_password": self.get_password_hash(user.password),
            "phone_number": user.phone_number,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        created_user = await self.repository.add_one(userdata)
        logger.debug("User crated: {}", created_user)
        return created_user.to_read_model()

    async def get_user_by_email(self, email: str) -> UserModel:
        """Get user by email.

        Args:
            email: `str`

        Return: `UserModel`

        Raise:
            `UserNotFoundExceptionError` if user not found
        """
        logger.debug("Find user by email: {}", email)
        filter = UserModel.email == email
        user = await self.repository.find_one(filter=filter)
        if user is None:
            raise UserNotFoundExceptionError()
        logger.debug("Returning user: {}", user)
        return user

    async def update_user(self, user_update: UserUpdate) -> UserSchema:
        user = await self.get_user_by_email(user_update.email)

        updated_user = await self.repository.update(
            where=UserModel.email == user.email, data=user_update.model_dump()
        )
        if updated_user is None:
            raise UserNotFoundExceptionError()

        return updated_user.to_read_model()

    async def get_user_bookings(self, user: UserSchema) -> list[BookingSchema]:
        bookings = await self.booking_service.get_user_bookings(user)
        return bookings

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
