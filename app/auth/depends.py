from auth.auth import ALGORITHM, SECRET_KEY
from auth.models import User
from database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        is_superuser: bool = payload.get("is_superuser", False)

    except JWTError:
        raise credentials_exception from JWTError

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    # Добавляем информацию о superuser в возвращаемого пользователя
    user.is_superuser = is_superuser
    return user


# Dependency для проверки superuser
def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user
