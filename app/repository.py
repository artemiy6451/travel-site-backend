from typing import Any, Generic, Type, TypeVar

from loguru import logger
from sqlalchemy import (
    ColumnElement,
    ColumnExpressionArgument,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Base

T = TypeVar("T", bound=Base)


class SQLAlchemyRepository(Generic[T]):
    def __init__(
        self, session: async_sessionmaker[AsyncSession], model: Type[T]
    ) -> None:
        self.session = session
        self.model = model
        logger.debug(
            "Setup repository with session: {} and model: {}", self.session, self.model
        )

    async def find_one(self, filter: ColumnElement[bool]) -> T | None:
        logger.debug(
            (
                "Send select request from `find_one`"
                "to database for model: {} with filter {}"
            ),
            self.model,
            filter,
        )

        async with self.session() as s:
            stmt = select(self.model).filter(filter)

            logger.debug("Final statement: {}", stmt)

            res = await s.execute(stmt)
            row = res.scalar_one_or_none()

            logger.debug("Returning from `find_one`: {}", row)

            return row

    async def find_all(
        self,
        join_by: Any | None = None,
        filter_by: ColumnElement[bool] | None = None,
        order_by: Any | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[T]:
        logger.debug(
            (
                "Send select request from `find_all` to database for model: {}"
                "with filter: {}, offset: {}, limit: {}, join: {}"
            ),
            self.model,
            filter_by,
            offset,
            limit,
            join_by,
        )

        async with self.session() as s:
            stmt = select(self.model)
            if join_by is not None:
                stmt = stmt.join(join_by)

            if filter_by is not None:
                stmt = stmt.where(filter_by)

            if order_by is not None:
                stmt = stmt.order_by(order_by)
            stmt = stmt.offset(offset).limit(limit)

            logger.debug("Final statement: {}", stmt)

            result = await s.execute(stmt)
            res = [row[0] for row in result.all()]

            logger.debug("Returning from `find_all`: {} excursions", len(res))

            return res

    async def add_one(self, data: dict[str, Any]) -> T:
        logger.debug(
            "Send create request form `add_one` to database for model: {} and data: {}",
            self.model,
            data,
        )
        async with self.session() as s:
            stmt = insert(self.model).values(**data).returning(self.model)

            logger.debug("Final statement: {}", stmt)

            res = await s.execute(stmt)
            await s.commit()
            result = res.scalar_one()

            logger.debug("Returning from `add_one`: {}", result)

            return result

    async def update(
        self,
        where: ColumnExpressionArgument,
        data: dict[str, Any],
    ) -> T | None:
        logger.debug(
            (
                "Send update request form `update` to database"
                "for model: {}, where: {} and data: {}"
            ),
            self.model,
            where,
            data,
        )

        async with self.session() as s:
            stmt = update(self.model).values(**data).where(where).returning(self.model)

            logger.debug("Final statement: {}", stmt)

            res = await s.execute(stmt)
            await s.commit()
            result = res.scalars().one_or_none()

            logger.debug("Returning from `update_one`: {}", result)

            return result

    async def update_all(
        self,
        where: ColumnExpressionArgument,
        data: dict[str, Any],
    ) -> list[T]:
        logger.debug(
            (
                "Send update request form `update_all` to database"
                "for model: {}, where: {} and data: {}"
            ),
            self.model,
            where,
            data,
        )

        async with self.session() as s:
            stmt = update(self.model).values(**data).where(where).returning(self.model)

            logger.debug("Final statement: {}", stmt)

            res = await s.execute(stmt)
            await s.commit()
            result = [row[0] for row in res.all()]

            logger.debug("Returning from `update_all`: {}", result)

            return result

    async def delete_one(self, id: int) -> int:
        logger.debug(
            "Send delete request form `delete_one` to database for model: {} and id: {}",
            self.model,
            id,
        )
        async with self.session() as s:
            stmt = delete(self.model).where(self.model.id == id).returning(self.model.id)
            logger.debug("Final statement: {}", stmt)
            res = await s.execute(stmt)
            await s.commit()
            result = res.scalar_one()

            logger.debug("Returning from `delete_one`: {}", result)

            return result
