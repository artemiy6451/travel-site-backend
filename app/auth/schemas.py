from pydantic import BaseModel, EmailStr, field_validator

MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 72


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LEN:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > MAX_PASSWORD_LEN:
            raise ValueError("Password must be less than 72 characters")
        return v


class UserSchema(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
