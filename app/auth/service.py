import datetime
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext

from app.auth.models import UserModel
from app.auth.schemas import Token, UserCreate, UserSchema
from app.config import settings
from app.database import async_session_maker
from app.repository import SQLAlchemyRepository

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self) -> None:
        self.repository: SQLAlchemyRepository[UserModel] = SQLAlchemyRepository(
            async_session_maker, UserModel
        )
        logger.debug("Setup UserService with repository: {}", self.repository)

    async def get_user_by_email(self, email: str) -> UserModel | None:
        logger.debug("Find user by email: {}", email)
        filter = UserModel.email == email
        user = await self.repository.find_one(filter=filter)
        logger.debug("Returning user: {!r}", user)
        return user if user else None

    async def create_user(self, user: UserCreate) -> UserSchema:
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

    async def authenticate_user(self, email: str, password: str) -> UserSchema:
        logger.debug(
            "Authentificate user with email={email!r} and password={password!r}",
            email=email,
            password=password,
        )
        user = await self.get_user_by_email(email=email)
        if not user:
            logger.warning(
                "Can not find user in database: email={email!r}, password={password!r}",
                email=email,
                password=password,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not self.verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            logger.warning(
                "Password hash doesn't match: email={email!r}, password={password!r}",
                email=email,
                password=password,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_schema = user.to_read_model()
        self.check_admin_user(user_schema)
        return user_schema

    def check_admin_user(self, user: UserSchema) -> bool:
        logger.debug(
            "Check admin access for user: {user!r}",
            user=user,
        )
        if not user.is_superuser:
            logger.warning(
                "No admin privileges for user: {user!r}",
                user=user,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required.",
            )
        return True

    def get_token(self, user: UserSchema) -> Token:
        logger.debug(
            "Get token for user: {user!r}",
            user=user,
        )
        access_token_expires = datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        )
        access_token = self.create_access_token(
            data={
                "sub": user.email,
                "is_superuser": user.is_superuser,
            },
            expires_delta=access_token_expires,
        )
        token = Token(access_token=access_token, token_type="bearer")
        logger.debug(
            "Returning token: {token!r}",
            token=token,
        )
        return token

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[datetime.timedelta] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
        else:
            expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                hours=24
            )
        to_encode.update(
            {"exp": expire, "is_superuser": data.get("is_superuser", False)}
        )
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> str:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            return email
        except JWTError:
            raise credentials_exception from JWTError
