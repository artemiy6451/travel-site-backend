from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.auth.depends import require_superuser
from app.config import settings
from app.images.depends import get_image_service
from app.images.schemas import ImageSchema
from app.images.service import ImageService
from app.user.schemas import UserSchema
from app.utils.cache import cached

image_router = APIRouter(tags=["Image"])


@cached(ttl=settings.ttl, key_prefix="excurion_excursion_images")
@image_router.get(
    "/images/{excursion_id}",
    response_model=list[ImageSchema],
)
async def get_excursion_images(
    excursion_id: int,
    service: Annotated[ImageService, Depends(get_image_service)],
) -> list[ImageSchema]:
    """Get excursion images by excursion id."""
    return await service.get_excursion_images(excursion_id=excursion_id)


@image_router.post(
    "/images/{excursion_id}",
    response_model=ImageSchema,
)
async def save_image(
    excursion_id: int,
    image_file: Annotated[UploadFile, File(...)],
    service: Annotated[ImageService, Depends(get_image_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ImageSchema:
    """Save excursion image."""
    return await service.save_excurion_image(image=image_file, excursion_id=excursion_id)


@image_router.delete("/images/{image_id}")
async def delete_excursion_image(
    image_id: int,
    service: Annotated[ImageService, Depends(get_image_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> bool:
    """Delete excursion image by image id."""
    return await service.delete_excursion_image(image_id=image_id)
