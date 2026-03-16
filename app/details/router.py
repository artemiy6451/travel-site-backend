from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth.depends import require_superuser
from app.config import settings
from app.details.depends import get_details_service
from app.details.exceptions import (
    ExcursionDetailsAlreadyExistError,
    ExcursionDetailsNotFoundError,
)
from app.details.schemas import (
    DetailsCreateScheme,
    DetailsScheme,
    DetailsUpdateScheme,
)
from app.details.service import DetailsService
from app.excursions.exceptions import ExcursionNotFoundError
from app.user.schemas import UserSchema
from app.utils.cache import cached

details_router = APIRouter(tags=["Details"])


# ===== Public ручки для работы с ExcursionDetailsModel =====
@cached(ttl=settings.ttl, key_prefix="excursion_details")
@details_router.get(
    "/details/{excursion_id}",
    response_model=DetailsScheme,
    responses={
        404: {"description": "Excursion details not found"},
    },
)
async def get_excursion_details(
    excursion_id: int,
    service: Annotated[DetailsService, Depends(get_details_service)],
) -> DetailsScheme:
    """Get excursion details by excursion id."""
    try:
        return await service.get_excursion_details(excursion_id=excursion_id)
    except ExcursionDetailsNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@details_router.post(
    "/details/{excursion_id}",
    response_model=DetailsScheme,
    responses={
        400: {"description": "Excursion details already exist"},
        404: {"description": "Excursion not found"},
    },
)
async def create_excursion_details(
    excursion_id: int,
    service: Annotated[DetailsService, Depends(get_details_service)],
    details: DetailsCreateScheme,
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> DetailsScheme:
    """Create excursion details."""
    try:
        return await service.create_excursion_details(
            excursion_id=excursion_id, details=details
        )
    except (
        ExcursionDetailsAlreadyExistError,
        ExcursionNotFoundError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@details_router.put(
    "/details/{excursion_id}",
    response_model=DetailsScheme,
    responses={
        404: {"description": "Excursion details not found"},
    },
)
async def update_excursion_details(
    excursion_id: int,
    details: DetailsUpdateScheme,
    service: Annotated[DetailsService, Depends(get_details_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> DetailsScheme:
    """Update excursion details by excursion id."""
    try:
        return await service.update_excursion_details(
            excursion_id=excursion_id, details_update=details
        )
    except (
        ExcursionDetailsNotFoundError,
        ExcursionNotFoundError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@details_router.delete(
    "/details/{excursion_id}",
    responses={
        404: {"description": "Excursion details not found"},
    },
)
async def delete_excursion_details(
    excursion_id: int,
    service: Annotated[DetailsService, Depends(get_details_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> dict:
    """Delete excursion details by excursion id."""
    try:
        await service.delete_excursion_details(excursion_id=excursion_id)
        return {"message": "Excursion details deleted successfully"}
    except (
        ExcursionDetailsNotFoundError,
        ExcursionNotFoundError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
