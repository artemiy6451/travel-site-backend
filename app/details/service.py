from loguru import logger

from app.database import async_session_maker
from app.details.exceptions import (
    ExcursionDetailsAlreadyExistError,
    ExcursionDetailsNotFoundError,
)
from app.details.models import DetailsModel
from app.details.schemas import (
    DetailsCreateScheme,
    DetailsScheme,
    DetailsUpdateScheme,
)
from app.excursions.service import ExcursionService
from app.repository import SQLAlchemyRepository
from app.utils.cache import invalidate_cache


class DetailsService:
    """Service for excursion details."""

    def __init__(self) -> None:
        """Create excursion service and details repository."""
        self.excursion_service = ExcursionService()

        self.details_repository: SQLAlchemyRepository[DetailsModel] = (
            SQLAlchemyRepository(async_session_maker, DetailsModel)
        )

    async def get_excursion_details(self, excursion_id: int) -> DetailsScheme:
        """Get excursion details by excursion id.

        Args:
            excursion_id: `int`

        Return: `ExcursionDetailsScheme`

        Raise: `ExcursionDetailsNotFoundError` if excursion details not found
        """
        logger.debug(
            "Get excursion details for excursion with id: {!r}",
            excursion_id,
        )

        details = await self.details_repository.find_one(
            filter=(DetailsModel.excursion_id == excursion_id)
        )
        if details is None:
            raise ExcursionDetailsNotFoundError()

        return details.to_read_model()

    @invalidate_cache(
        "excursion_details*",
        "excursion_full*",
    )
    async def create_excursion_details(
        self, excursion_id: int, details: DetailsCreateScheme
    ) -> DetailsScheme:
        """Create excursion details.

        Args:
            excursion_id: `int`
            details: `ExcursionDetailsCreateScheme`

        Return: `ExcursionDetailsScheme`

        Raise: `ExcursionDetailsAlreadyExistError` if excursion details already exist
        """
        logger.debug(
            (
                "Create excursion details for excursion with id={id!r}"
                "and deatils={details!r}"
            ),
            id=excursion_id,
            details=details,
        )

        await self.excursion_service.get_excursion(excursion_id)
        old_details = await self.details_repository.find_one(
            filter=(DetailsModel.excursion_id == excursion_id)
        )
        if old_details:
            raise ExcursionDetailsAlreadyExistError()

        creation_data = {**details.model_dump()}
        creation_data["excursion_id"] = excursion_id

        new_details = await self.details_repository.add_one(data=creation_data)
        return new_details.to_read_model()

    @invalidate_cache(
        "excursion_details*",
        "excursion_full*",
    )
    async def update_excursion_details(
        self, excursion_id: int, details_update: DetailsUpdateScheme
    ) -> DetailsScheme:
        """Update excursion details by excursion id.

        Args:
            excursion_id: `int`
            details_update: `ExcursionDetailsUpdateScheme`

        Return: `ExcursionDetailsScheme`

        Raise: `ExcursionDetailsNotFoundError` if excursion details not found
        """
        logger.debug(
            (
                "Update excursion details for excursion with id={id!r}"
                "and deatils={details!r}"
            ),
            id=excursion_id,
            details=details_update,
        )

        await self.excursion_service.get_excursion(excursion_id)
        details = await self.get_excursion_details(excursion_id=excursion_id)

        updated_details = await self.details_repository.update(
            where=DetailsModel.id == details.id,
            data=details_update.model_dump(),
        )
        if updated_details is None:
            raise ExcursionDetailsNotFoundError()

        return updated_details.to_read_model()

    @invalidate_cache("excursion_details*", "excursion_full*", "excursion_with_details*")
    async def delete_excursion_details(self, excursion_id: int) -> bool:
        """Delete excursion details by excursion id.

        Args:
            excursion_id: `int`

        Return: `bool`

        Raise: `ExcursionDetailsNotFoundError` if excursion details not found
        """
        logger.debug(
            "Delete excursion details for excursion with id: {!r}", excursion_id
        )

        details = await self.get_excursion_details(excursion_id=excursion_id)
        details_id = await self.details_repository.delete_one(id=details.id)
        if details_id is None:
            raise ExcursionDetailsNotFoundError()

        return True
