from fastapi import status

from app.exceptions import ServiceError


class ExcursionDetailsNotFoundError(ServiceError):
    """Excursion details not found."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Excursion details not found"


class ExcursionDetailsAlreadyExistError(ServiceError):
    """Excursion details already exist."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Excursion details already exist"
