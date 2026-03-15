"""File with excursion service."""

from datetime import datetime

from loguru import logger

from app.database import async_session_maker
from app.excursions.exceptions import (
    ExcursionAddPeopleOverflowError,
    ExcursionBusNumberNegativeError,
    ExcursionNotFoundError,
)
from app.excursions.models import (
    ExcursionModel,
)
from app.excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionScheme,
    ExcursionType,
    ExcursionUpdateScheme,
)
from app.repository import SQLAlchemyRepository
from app.utils.cache import invalidate_cache


class ExcursionService:
    """Service for excursion models."""

    def __init__(self) -> None:
        """Create excursion repository and details service."""
        self.excursion_repository: SQLAlchemyRepository[ExcursionModel] = (
            SQLAlchemyRepository(async_session_maker, ExcursionModel)
        )

    async def get_excursion(self, excursion_id: int) -> ExcursionScheme:
        """Get excursion by id.

        Args:
            excursion_id: `int`

        Return: `ExcursionScheme`

        Raise: `ExcursionNotFoundError` if excursion not found
        """
        logger.debug("Get excursion with id: {id!r}", id=excursion_id)

        excursion = await self.excursion_repository.find_one(
            filter=ExcursionModel.id == excursion_id,
        )
        if excursion is None:
            raise ExcursionNotFoundError()

        return excursion.to_read_model()

    async def get_active_excursions(
        self,
        offset: int = 0,
        limit: int = 100,
        excursion_type: ExcursionType = ExcursionType.EXCURSION,
    ) -> list[ExcursionScheme]:
        """Get active excursions by offset, limit and excursion type.

        Args:
            offset: `int`
            limit: `int`
            excursion_type: `ExcursionType`

        Return: `list[ExcursionScheme]`
        """
        logger.debug(
            "Get active excursions with offset={!r}, limit={!r} and excursion_type={!r}",
            offset,
            limit,
            excursion_type,
        )
        filter_by = (ExcursionModel.is_active == True) & (  # noqa: E712
            ExcursionModel.type == excursion_type
        )
        excursions = await self.excursion_repository.find_all(
            offset=offset,
            limit=limit,
            filter_by=filter_by,
            order_by=ExcursionModel.date,
        )
        return [excursion.to_read_model() for excursion in excursions]

    async def get_not_active_excursions(
        self,
        offset: int = 0,
        limit: int = 100,
        excursion_type: ExcursionType = ExcursionType.EXCURSION,
    ) -> list[ExcursionScheme]:
        """Get not active excursions by offset, limit and excursion type.

        Args:
            offset: `int`
            limit: `int`
            excursion_type: `ExcursionType`

        Return: `list[ExcursionScheme]`
        """
        logger.debug(
            "Get not active excursions with offset={!r},"
            " limit={!r} and excursion_type={!r}",
            offset,
            limit,
            excursion_type,
        )

        filter_by = (ExcursionModel.is_active == False) & (  # noqa: E712
            ExcursionModel.type == excursion_type
        )
        excursions = await self.excursion_repository.find_all(
            offset=offset, limit=limit, order_by=ExcursionModel.date, filter_by=filter_by
        )
        return [excursion.to_read_model() for excursion in excursions]

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def create_excursion(
        self, excursion: ExcursionCreateScheme
    ) -> ExcursionScheme:
        """Create excursion.

        Args:
            excursion: `ExcursionCreateScheme`

        Return: `ExcursionScheme`
        """
        logger.debug("Create excursion: {!r}", excursion)

        created_excursion = await self.excursion_repository.add_one(
            excursion.model_dump()
        )
        return created_excursion.to_read_model()

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def update_excursion(
        self, excursion_id: int, excursion_update: ExcursionUpdateScheme
    ) -> ExcursionScheme:
        """Update excursion by excursion id.

        Args:
            excursion_id: `int`
            excursion_update: `ExcursionUpdateScheme`

        Return: `ExcursionScheme`

        Raise: `ExcursionNotFoundError` if excursion not found
        """
        logger.debug(
            "Create excursion with id {id!r} and data: {data!r}",
            id=excursion_id,
            data=excursion_update,
        )

        await self.get_excursion(excursion_id)

        new_excursion = await self.excursion_repository.update(
            where=ExcursionModel.id == excursion_id,
            data=excursion_update.model_dump(),
        )
        if new_excursion is None:
            raise ExcursionNotFoundError()

        return new_excursion.to_read_model()

    async def search_excursions(self, search_term: str) -> list[ExcursionScheme]:
        """Search excursion by search term.

        Args:
            search_term: `str`

        Return: `list[ExcursionScheme]`
        """
        logger.debug("Search excursion by serch term: {!r}", search_term)

        filter = ExcursionModel.title.ilike(
            f"%{search_term}%"
        ) | ExcursionModel.description.ilike(f"%{search_term}%")
        excursions = await self.excursion_repository.find_all(filter_by=filter)

        return [excursion.to_read_model() for excursion in excursions]

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def delete_excursion(self, excursion_id: int) -> bool:
        """Delete excursion by excursion id.

        Args:
            excursion_id: `int`

        Return: `bool`

        Raise: `ExcursionNotFoundError` if excursion not found
        """
        logger.debug("Delete excursion with id: {!r}", excursion_id)

        excursion = await self.excursion_repository.delete_one(id=excursion_id)
        if excursion is None:
            raise ExcursionNotFoundError()
        return True

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def toggle_excursion_activity(self, excursion_id: int) -> ExcursionScheme:
        """Toggle excursion activity by excursion id.

        Args:
            excursion_id: `int`

        Return: `ExcursionScheme`

        Raise: `ExcursionNotFoundError` if excursion not found
        """
        logger.debug("Toggle excursion activity with id: {!r}", excursion_id)

        excursion = await self.get_excursion(excursion_id)
        updated_excursion = await self.excursion_repository.update(
            where=ExcursionModel.id == excursion_id,
            data={"is_active": not excursion.is_active},
        )
        if updated_excursion is None:
            raise ExcursionNotFoundError()

        return updated_excursion.to_read_model()

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def change_people_left_count(
        self, excursion_id: int, count_people: int
    ) -> ExcursionScheme:
        """Change people left count by excursion id.

        Args:
            excursion_id: `int`
            count_people: `int`

        Return: `ExcursionScheme`

        Raise:
            `ExcursionNotFoundError` if excursion not found
            `ExcursionAddPeopleOverflowError` if people left overflow
        """
        logger.debug(
            (
                "Add people left for excursion with id={id!r}"
                "and count people={count_people!r}"
            ),
            id=excursion_id,
            count_people=count_people,
        )

        excursion = await self.get_excursion(excursion_id)

        left = excursion.people_left - count_people
        if left < 0:
            raise ExcursionAddPeopleOverflowError()

        updated_excursion = await self.excursion_repository.update(
            where=ExcursionModel.id == excursion_id,
            data={"people_left": left},
        )
        if updated_excursion is None:
            raise ExcursionNotFoundError()
        return updated_excursion.to_read_model()

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def change_bus_number(
        self, excursion_id: int, bus_number: int
    ) -> ExcursionScheme:
        """Change bus number by excursion id.

        Args:
            excursion_id: `int`
            bus_number: `int`

        Return: `ExcursionScheme`

        Raise:
            `ExcursionNotFoundError` if excursion not found
            `ExcursionBusNumberNegativeError` if bus number negative
        """
        logger.debug(
            (
                "Change bus number for excursion with id={id!r}"
                "and bus_number={bus_number!r}"
            ),
            id=excursion_id,
            bus_number=bus_number,
        )

        await self.get_excursion(excursion_id)

        if bus_number < 0:
            raise ExcursionBusNumberNegativeError()

        updated_excursion = await self.excursion_repository.update(
            where=ExcursionModel.id == excursion_id,
            data={"bus_number": bus_number},
        )
        if updated_excursion is None:
            raise ExcursionNotFoundError()

        return updated_excursion.to_read_model()

    async def get_excursions_with_expired_date(self) -> list[ExcursionScheme]:
        """Get excursions with expired date.

        Return: `list[ExcursionScheme]`
        """
        logger.debug("Get excursions with expired date")

        excursions = await self.excursion_repository.find_all(
            filter_by=ExcursionModel.date < datetime.now()
        )

        return [excursion.to_read_model() for excursion in excursions]

    async def deactivate_past_excurions(self) -> bool:
        """Deactivate past excursions.

        Return: `bool`
        """
        where = (ExcursionModel.date < datetime.now()) & (ExcursionModel.is_active)
        updated_excursions = await self.excursion_repository.update(
            where=where,
            data={"is_active": False},
        )

        return True if updated_excursions else False
