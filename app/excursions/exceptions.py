"""Excursion exceptions file."""

from fastapi import status

from app.exceptions import ServiceError


class ExcursionNotFoundError(ServiceError):
    """Excursion not found."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Excursion not found"


class ExcursionAddPeopleOverflowError(ServiceError):
    """Excursion add people error."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Can not add people, owerflow"


class ExcursionBusNumberNegativeError(ServiceError):
    """Excursion bus number error."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Bus number can not be under zero"
