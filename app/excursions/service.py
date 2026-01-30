from fastapi import HTTPException, UploadFile, status
from loguru import logger

from app.cache import invalidate_cache
from app.database import async_session_maker
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
    ExcursionUpdateScheme,
)
from app.repository import SQLAlchemyRepository


class ExcurionService:
    def __init__(self) -> None:
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
        logger.debug("Get excursion with id: {id!r}", id=excursion_id)

        excursion = await self.excursion_repository.find_one(
            filter=ExcursionModel.id == excursion_id
        )
        if excursion is None:
            raise HTTPException(status_code=404, detail="Excursion not found")

        return excursion.to_read_model()

    async def get_active_excursions(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ExcursionScheme]:
        logger.debug(
            "Get active excursions with offset={!r} and limit={!r}", offset, limit
        )
        filter_by = ExcursionModel.is_active == True  # noqa: E712
        excursions = await self.excursion_repository.find_all(
            offset=offset, limit=limit, filter_by=filter_by, order_by=ExcursionModel.date
        )
        return [excursion.to_read_model() for excursion in excursions]

    async def get_not_active_excursions(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ExcursionScheme]:
        logger.debug(
            "Get not active excursions with offset={!r} and limit={!r}", offset, limit
        )

        filter_by = ExcursionModel.is_active == False  # noqa: E712
        excursions = await self.excursion_repository.find_all(
            offset=offset, limit=limit, order_by=ExcursionModel.date, filter_by=filter_by
        )
        return [excursion.to_read_model() for excursion in excursions]

    async def get_excursion_images(
        self, excursion_id: int
    ) -> list[ExcursionImageSchema]:
        logger.debug("Get excursion images for id={!r}", excursion_id)

        images = await self.images_repository.find_all(
            filter_by=(ExcursionImageModel.excursion_id == excursion_id)
        )
        return [image.to_read_model() for image in images]

    async def get_excursion_details(self, excursion_id: int) -> ExcursionDetailsScheme:
        logger.debug(
            "Get excursion details for excursion with id: {!r}",
            excursion_id,
        )

        details = await self.details_repository.find_one(
            filter=(ExcursionDetailsModel.excursion_id == excursion_id)
        )
        if details is None:
            raise HTTPException(status_code=404, detail="Excursion details not found")

        return details.to_read_model()

    async def get_excursion_full_info(self, excursion_id: int) -> ExcursionFullScheme:
        logger.debug(
            "Get full info about excursion with id: {!r}",
            excursion_id,
        )

        excursion = await self.get_excursion(excursion_id)
        details = await self.get_excursion_details(excursion_id)
        images = await self.get_excursion_images(excursion_id)

        result = ExcursionFullScheme(
            title=excursion.title,
            description=excursion.description,
            date=excursion.date,
            price=excursion.price,
            bus_number=excursion.bus_number,
            people_amount=excursion.people_amount,
            people_left=excursion.people_left,
            is_active=excursion.is_active,
            id=excursion.id,
        )

        if details:
            result.details = details
        if images:
            result.images = images

        return result

    async def add_excurion_image(
        self, image: UploadFile, excursion_id: int
    ) -> ExcursionImageSchema:
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
        logger.debug("Create excursion: {!r}", excursion)

        if await self.search_excursions(excursion.title):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excursion already exist",
            )
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
            raise HTTPException(
                status_code=404, detail="Excursion details already exist"
            )

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
        logger.debug(
            "Create excursion with id {id!r} and data: {data!r}",
            id=excursion_id,
            data=excursion_update,
        )

        await self.get_excursion(excursion_id)

        new_excursion = await self.excursion_repository.update_one(
            id=excursion_id, data=excursion_update.model_dump()
        )
        return new_excursion.to_read_model()

    @invalidate_cache(
        "excursion_details*",
        "excursion_full*",
    )
    async def update_excursion_details(
        self, excursion_id: int, details_update: ExcursionDetailsUpdateScheme
    ) -> ExcursionDetailsScheme:
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

        updated_details = await self.details_repository.update_one(
            id=details.id, data=details_update.model_dump()
        )
        return updated_details.to_read_model()

    async def search_excursions(self, search_term: str) -> list[ExcursionScheme]:
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
        logger.debug("Delete excursion with id: {!r}", excursion_id)

        await self.excursion_repository.delete_one(id=excursion_id)
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
        logger.debug(
            "Delete image with id={id!r}",
            id=image_id,
        )
        image = await self.images_repository.find_one(
            filter=(ExcursionImageModel.id == image_id)
        )
        if image is None:
            return False

        delete_uploaded_file_by_url(image.url)

        await self.images_repository.delete_one(id=image_id)
        return True

    @invalidate_cache("excursion_details*", "excursion_full*", "excursion_with_details*")
    async def delete_excursion_details(self, excursion_id: int) -> bool:
        logger.debug(
            "Delete excursion details for excursion with id: {!r}", excursion_id
        )

        details = await self.get_excursion_details(excursion_id=excursion_id)
        await self.details_repository.delete_one(id=details.id)
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
        logger.debug("Toggle excursion activity with id: {!r}", excursion_id)

        excursion = await self.get_excursion(excursion_id)

        updated_excursion = await self.excursion_repository.update_one(
            id=excursion_id, data={"is_active": not excursion.is_active}
        )

        return updated_excursion.to_read_model()

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def change_people_left(
        self, excursion_id: int, count_people: int
    ) -> ExcursionScheme:
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
            raise HTTPException(
                status_code=405,
                detail=f"Can not add {count_people} people, owerflow.",
            )

        updated_excursion = await self.excursion_repository.update_one(
            id=excursion_id, data={"people_left": left}
        )
        return updated_excursion.to_read_model()

    @invalidate_cache(
        "not_active_excursions*",
        "active_excursions*",
        "excurion_excursion_images*",
        "excursions_search*",
        "excursion_details*",
        "excursion_full*",
    )
    async def change_bus_number_crud(
        self, excursion_id: int, bus_number: int
    ) -> ExcursionScheme:
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Номер автобуса не может быть отрицательным",
            )

        updated_excursion = await self.excursion_repository.update_one(
            id=excursion_id, data={"bus_number": bus_number}
        )
        return updated_excursion.to_read_model()

    def __repr__(self) -> str:
        return "ExcurionService"
