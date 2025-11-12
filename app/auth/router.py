from datetime import timedelta

from auth.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from auth.crud import authenticate_user, create_user, get_user_by_email
from auth.depends import get_current_user, require_superuser
from auth.models import User
from auth.schemas import Token, UserCreate
from auth.schemas import User as UserSchema
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

login_router = APIRouter(tags=["Auth API"])


# Регистрация пользователя
@login_router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)) -> UserSchema:
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    return create_user(db, user)


# Авторизация и получение токена
@login_router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)) -> Token:
    authenticated_user = authenticate_user(db, user.email, user.password)
    if authenticated_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем, что пользователь - суперюзер
    if not authenticated_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": authenticated_user.email,
            "is_superuser": authenticated_user.is_superuser,
        },
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@login_router.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)) -> UserSchema:
    return current_user


@login_router.get("/admin/check-access")
def check_admin_access(current_user: User = Depends(require_superuser)) -> dict:
    return {
        "status": "success",
        "message": "Admin access granted",
        "user": current_user.email,
    }
