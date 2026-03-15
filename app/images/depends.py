from app.images.service import ImageService


async def get_image_service() -> ImageService:
    return ImageService()
