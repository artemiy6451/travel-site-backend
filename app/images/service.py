from fastapi import UploadFile
from loguru import logger

from app.database import async_session_maker
from app.images.exceptions import ImageNotFoundError
from app.images.files import delete_uploaded_file_by_url, save_uploaded_file
from app.images.models import ImageModel
from app.images.schemas import ImageSchema
from app.repository import SQLAlchemyRepository
from app.utils.cache import invalidate_cache


class ImageService:
    def __init__(self) -> None:
        self.images_repository: SQLAlchemyRepository[ImageModel] = SQLAlchemyRepository(
            async_session_maker, ImageModel
        )

    async def get_excursion_images(self, excursion_id: int) -> list[ImageSchema]:
        """Get excursion images by excursion id.

        Args:
            excursion_id: `int`

        Return: `list[ExcursionImageSchema]`
        """
        logger.debug("Get excursion images for id={!r}", excursion_id)

        images = await self.images_repository.find_all(
            filter_by=(ImageModel.excursion_id == excursion_id)
        )
        return [image.to_read_model() for image in images]

    async def save_excurion_image(
        self, image: UploadFile, excursion_id: int
    ) -> ImageSchema:
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
        image = await self.images_repository.find_one(filter=(ImageModel.id == image_id))
        if image is None:
            raise ImageNotFoundError()

        delete_uploaded_file_by_url(image.url)

        deleted_image_id = await self.images_repository.delete_one(id=image_id)
        if deleted_image_id is None:
            raise ImageNotFoundError()

        return True
