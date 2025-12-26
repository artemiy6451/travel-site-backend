from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.depends import get_current_user, get_user_service
from app.auth.schemas import Token, UserCreate, UserSchema
from app.auth.service import UserService

login_router = APIRouter(tags=["Auth"])


# Регистрация пользователя
@login_router.post("/register", response_model=UserSchema)
async def register(
    user: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
) -> UserSchema:
    created_user = await service.create_user(user)
    return created_user


# Авторизация и получение токена
@login_router.post("/login", response_model=Token)
async def login(
    user: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
) -> Token:
    authenticated_user = await service.authenticate_user(user.email, user.password)
    token = service.get_token(authenticated_user)
    return token


@login_router.get("/users/me", response_model=UserSchema)
def read_users_me(user: Annotated[UserSchema, Depends(get_current_user)]) -> UserSchema:
    return user
