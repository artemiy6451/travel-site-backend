from pydantic import BaseModel


class Token(BaseModel):
    """Token schema.

    Attributes:
        access_token: Access token
        token_type: Token type
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema.

    Attributes:
        email: User email
    """

    email: str | None = None
