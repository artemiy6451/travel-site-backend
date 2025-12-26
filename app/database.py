from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings

settings = Settings()

logger.debug("Setup database with uri %s", settings.database_uri)
async_engine = create_async_engine(
    settings.database_uri,
    poolclass=NullPool,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        logger.debug("Database setup complete")
        yield session
