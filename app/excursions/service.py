"""File with excursion service."""

from datetime import datetime

from fastapi import UploadFile
from loguru import logger

from app.database import async_session_maker
from app.excursions.exceptions import (
    ExcursionAddPeopleOverflowError,
    ExcursionBusNumberNegativeError,
    ExcursionDetailsAlreadyExistError,
    ExcursionDetailsNotFoundError,
    ExcursionImageNotFoundError,
    ExcursionNotFoundError,
)
from app.excursions.files import delete_uploaded_file_by_url, save_uploaded_file
from app.excursions.models import (
    ExcursionDetailsModel,
    ExcursionImageModel,
    ExcursionModel,
)
from app.excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionDetailsCreateScheme,
    ExcursionDetailsScheme,
    ExcursionDetailsUpdateScheme,
    ExcursionFullScheme,
    ExcursionImageSchema,
    ExcursionScheme,
    ExcursionType,
    ExcursionUpdateScheme,
)
from app.repository import SQLAlchemyRepository
from app.utils.cache import invalidate_cache


class ExcursionService:
    """Service for excursion models."""

    def __init__(self) -> None:
        """Create excursion, details and images repository."""
        self.excursion_repository: SQLAlchemyRepository[ExcursionModel] = (
            SQLAlchemyRepository(async_session_maker, ExcursionModel)
        )
        self.details_repository: SQLAlchemyRepository[ExcursionDetailsModel] = (
            SQLAlchemyRepository(async_session_maker, ExcursionDetailsModel)
        )
        self.images_repository: SQLAlchemyRepository[ExcursionImageModel] = (
            SQLAlchemyRepository(async_session_maker, ExcursionImageModel)
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

    async def get_excursion_images(
        self, excursion_id: int
    ) -> list[ExcursionImageSchema]:
        """Get excursion images by excursion id.

        Args:
            excursion_id: `int`

        Return: `list[ExcursionImageSchema]`
        """
        logger.debug("Get excursion images for id={!r}", excursion_id)

        images = await self.images_repository.find_all(
            filter_by=(ExcursionImageModel.excursion_id == excursion_id)
        )
        return [image.to_read_model() for image in images]

    async def get_excursion_details(self, excursion_id: int) -> ExcursionDetailsScheme:
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
            filter=(ExcursionDetailsModel.excursion_id == excursion_id)
        )
        if details is None:
            raise ExcursionDetailsNotFoundError()

        return details.to_read_model()

    async def get_excursion_full_info(self, excursion_id: int) -> ExcursionFullScheme:
        """Get full info about excursion by excursion id.

        Args:
            excursion_id: `int`

        Return: `ExcursionFullScheme`
        """
        logger.debug(
            "Get full info about excursion with id: {!r}",
            excursion_id,
        )

        excursion = await self.get_excursion(excursion_id)
        details = await self.get_excursion_details(excursion_id)
        images = await self.get_excursion_images(excursion_id)

        result = ExcursionFullScheme(
            type=excursion.type,
            title=excursion.title,
            description=excursion.description,
            date=excursion.date,
            price=excursion.price,
            bus_number=excursion.bus_number,
            people_amount=excursion.people_amount,
            people_left=excursion.people_left,
            is_active=excursion.is_active,
            id=excursion.id,
            cities=excursion.cities,
        )

        if details:
            result.details = details
        if images:
            result.images = images

        return result

    async def save_excurion_image(
        self, image: UploadFile, excursion_id: int
    ) -> ExcursionImageSchema:
        """Save image for excursion by excursion id.

        Args:
            image: `UploadFile`
            excursion_id: `int`

        Return: `ExcursionImageSchema`
        """
        logger.debug(
            "Add image {image!r} for excursion with id={id!r}",
            image=image,
            id=excursion_id,
        )

        url = save_uploaded_file(file=image)
        data = {
            "excursion_id": excursion_id,
            "url": url,
        }
        new_image = await self.images_repository.add_one(data)
        return new_image.to_read_model()

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
        "excursion_details*",
        "excursion_full*",
    )
    async def create_excursion_details(
        self, excursion_id: int, details: ExcursionDetailsCreateScheme
    ) -> ExcursionDetailsScheme:
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

        await self.get_excursion(excursion_id)
        old_details = await self.details_repository.find_one(
            filter=(ExcursionDetailsModel.excursion_id == excursion_id)
        )
        if old_details:
            raise ExcursionDetailsAlreadyExistError()

        creation_data = {**details.model_dump()}
        creation_data["excursion_id"] = excursion_id

        new_details = await self.details_repository.add_one(data=creation_data)
        return new_details.to_read_model()

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

    @invalidate_cache(
        "excursion_details*",
        "excursion_full*",
    )
    async def update_excursion_details(
        self, excursion_id: int, details_update: ExcursionDetailsUpdateScheme
    ) -> ExcursionDetailsScheme:
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

        await self.get_excursion(excursion_id)
        details = await self.get_excursion_details(excursion_id=excursion_id)

        updated_details = await self.details_repository.update(
            where=ExcursionDetailsModel.id == details.id,
            data=details_update.model_dump(),
        )
        if updated_details is None:
            raise ExcursionDetailsNotFoundError()

        return updated_details.to_read_model()

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
    async def delete_excursion_image(self, image_id: int) -> bool:
        """Delete excursion image by image id.

        Args:
            image_id: `int`

        Return: `bool`

        Raise: `ExcursionImageNotFoundError` if excursion image not found
        """
        logger.debug(
            "Delete image with id={id!r}",
            id=image_id,
        )
        image = await self.images_repository.find_one(
            filter=(ExcursionImageModel.id == image_id)
        )
        if image is None:
            raise ExcursionImageNotFoundError()

        delete_uploaded_file_by_url(image.url)

        deleted_image_id = await self.images_repository.delete_one(id=image_id)
        if deleted_image_id is None:
            raise ExcursionImageNotFoundError()

        return True

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
