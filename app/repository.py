from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy import (
    ColumnElement,
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

    async def find_one(self, filter: ColumnElement) -> T | None:
        async with self.session() as s:
            stmt = select(self.model).filter(filter)
            res = await s.execute(stmt)
            row = res.scalar_one_or_none()
            return row

    async def find_all(
        self,
        filter_by: Optional[Any] = None,
        join_by: Optional[tuple[Any, Any, Any]] = None,
    ) -> list[T]:
        async with self.session() as s:
            stmt = select(self.model)
            if join_by:
                stmt = select(self.model, join_by[1])
                stmt = stmt.select_from(join_by[0]).join(*join_by[1:])
            if filter_by is not None:
                stmt = stmt.where(filter_by)

            result = await s.execute(stmt)
            res = [row[0] for row in result.all()]
            return res

    async def add_one(self, data: dict[str, Any]) -> T:
        async with self.session() as s:
            stmt = insert(self.model).values(**data).returning(self.model)
            res = await s.execute(stmt)
            await s.commit()
            return res.scalar_one()

    async def update_one(self, id: int, data: dict[str, Any]) -> T | None:
        async with self.session() as s:
            stmt = (
                update(self.model)
                .values(**data)
                .where(self.model.id == id)
                .returning(self.model)
            )
            res = await s.execute(stmt)
            await s.commit()
            return res.scalar_one_or_none()

    async def delete_one(self, id: int) -> int:
        async with self.session() as s:
            stmt = delete(self.model).where(self.model.id == id).returning(self.model.id)
            res = await s.execute(stmt)
            await s.commit()
            return res.scalar_one()
