import datetime
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
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
        self.user_repository: SQLAlchemyRepository[UserModel] = SQLAlchemyRepository(
            async_session_maker, UserModel
        )

    async def get_user_by_email(self, email: str) -> UserModel | None:
        filter = UserModel.email == email
        user = await self.user_repository.find_one(filter=filter)
        return user if user else None

    async def create_user(self, user: UserCreate) -> UserSchema:
        exist_user = await self.get_user_by_email(user.email)
        if exist_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        userdata = {
            "email": user.email,
            "hashed_password": self.get_password_hash(user.password),
        }
        created_user = await self.user_repository.add_one(userdata)
        return created_user.to_read_model()

    async def authenticate_user(self, email: str, password: str) -> UserSchema:
        user = await self.get_user_by_email(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not self.verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.to_read_model()

    def check_admin_user(self, user: UserSchema) -> bool:
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required.",
            )
        return True

    def get_token(self, user: UserSchema) -> Token:
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
        return Token(access_token=access_token, token_type="bearer")

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
