"""File with auth schemas."""

from pydantic import BaseModel, EmailStr, field_validator

MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 72


class UserBase(BaseModel):
    """User base schema.

    Attributes:
        email: User email
        phone_number: User phone number
    """

    email: EmailStr


class UserCreate(UserBase):
    """User create schema.

    Attributes:
        password: User password
    """

    password: str

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password length."""
        if len(v) < MIN_PASSWORD_LEN:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > MAX_PASSWORD_LEN:
            raise ValueError("Password must be less than 72 characters")
        return v


class UserLogin(BaseModel):
    """User login schema with email and password only."""

    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password length."""
        if len(v) < MIN_PASSWORD_LEN:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > MAX_PASSWORD_LEN:
            raise ValueError("Password must be less than 72 characters")
        return v


class UserSchema(UserBase):
    """User schema.

    Attributes:
        id: User id
        is_active: User is active
        is_superuser: User is superuser
    """

    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        """Pydantic config."""

        from_attributes = True
