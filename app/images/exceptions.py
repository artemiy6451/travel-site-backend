from fastapi import status

from app.exceptions import ServiceError


class ImageNotFoundError(ServiceError):
    """Excursion image not found."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Excursion image not found"
