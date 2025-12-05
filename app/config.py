import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mode: Literal["development", "production"] = Field(default="development")

    api_base_url: str = Field(default="")

    db_host: str = ""
    db_port: str = ""
    db_name: str = ""
    db_user: str = ""
    db_pass: str = ""

    secret_key: str = Field(default="")
    access_token_expire_minutes: int = Field(default=30)

    upload_dir: Path = Field(default=Path("static/"))

    ttl: int = Field(default=300)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.mode == "production"

    @property
    def is_development(self) -> bool:
        return self.mode == "development"

    @property
    def cors_origins(self) -> list:
        """CORS origins в зависимости от режима"""
        if self.is_development:
            return [
                "*",
            ]
        else:
            return ["https://travelvv.ru"]


settings = Settings()

os.makedirs(os.path.join(os.getcwd(), settings.upload_dir), exist_ok=True)
