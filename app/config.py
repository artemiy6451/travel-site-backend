import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mode: Literal["development", "production"] = Field(default="development")
    api_base_url: str = Field(default="")
    database_url: str = Field(default="")
    secret_key: str = Field(default="")
    access_token_expire_minutes: int = Field(default=30)
    upload_dir: str = Field(default="static/")
    ttl: int = Field(default=300)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

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
            # В production укажите ваш домен
            return ["https://travelvv.ru"]

    @property
    def upload_path(self) -> str:
        """Полный путь к директории загрузок"""
        return os.path.join(os.getcwd(), self.upload_dir)


# Создаем глобальный экземпляр конфигурации
settings = Settings()

# Создаем директорию для загрузок при инициализации
os.makedirs(settings.upload_path, exist_ok=True)
