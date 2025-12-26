import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.depends import get_current_user, get_user_service
from app.auth.schemas import UserSchema
from app.auth.service import UserService


@pytest.mark.asyncio
async def test_get_user_service():
    assert type(await get_user_service()) is UserService


@pytest.mark.asyncio
async def test_get_current_user():
    service = await get_user_service()
    token = service.get_token(
        user=UserSchema(email="me@lokach.ru", id=1, is_active=True, is_superuser=True)
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=token.access_token
    )

    result = await get_current_user(credentials=credentials, service=service)

    assert result.email is not None
