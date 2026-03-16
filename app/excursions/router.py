"""File with excursion router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.depends import require_superuser
from app.config import settings
from app.excursions.depends import get_excursion_service
from app.excursions.exceptions import (
    ExcursionAddPeopleOverflowError,
    ExcursionBusNumberNegativeError,
    ExcursionNotFoundError,
)
from app.excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionScheme,
    ExcursionType,
    ExcursionUpdateScheme,
)
from app.excursions.service import ExcursionService
from app.user.schemas import UserSchema
from app.utils.cache import cached

excursion_router = APIRouter(tags=["Excursion"])


@cached(ttl=settings.ttl, key_prefix="active_excursions")
@excursion_router.get(
    "/excursions/active",
    response_model=list[ExcursionScheme],
)
async def get_active_excursions(
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    skip: int = 0,
    limit: int = 100,
    excursion_type: ExcursionType = ExcursionType.EXCURSION,
) -> list[ExcursionScheme]:
    """Get active excursions by offset, limit and excursion type."""
    return await service.get_active_excursions(
        offset=skip,
        limit=limit,
        excursion_type=excursion_type,
    )


@cached(ttl=settings.ttl, key_prefix="not_active_excursions")
@excursion_router.get(
    "/excursions/not_active",
    response_model=list[ExcursionScheme],
)
async def get_not_active_excursions(
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
    skip: int = 0,
    limit: int = 100,
    excursion_type: ExcursionType = ExcursionType.EXCURSION,
) -> list[ExcursionScheme]:
    """Get not active excursions by offset, limit and excursion type."""
    return await service.get_not_active_excursions(
        offset=skip,
        limit=limit,
        excursion_type=excursion_type,
    )


@excursion_router.get(
    "/excursions/{excursion_id}",
    response_model=ExcursionScheme,
    responses={
        404: {"description": "Excursion not found"},
    },
)
async def read_excursion(
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    excursion_id: int,
) -> ExcursionScheme:
    """Get excursion by id."""
    try:
        return await service.get_excursion(excursion_id=excursion_id)
    except ExcursionNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@cached(ttl=settings.ttl, key_prefix="excursions_search")
@excursion_router.get(
    "/excursions/search/",
    response_model=list[ExcursionScheme],
)
async def search_excursions_by_term(
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    q: str = Query(...),
) -> list[ExcursionScheme]:
    """Search excursions by term."""
    return await service.search_excursions(search_term=q)


@excursion_router.post("/excursions", response_model=ExcursionScheme)
async def create_new_excursion(
    excursion: ExcursionCreateScheme,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    """Create new excursion."""
    new_excursion = await service.create_excursion(excursion=excursion)
    return new_excursion


@excursion_router.put(
    "/excursions/{excursion_id}",
    response_model=ExcursionScheme,
    responses={
        404: {"description": "Excursion not found"},
    },
)
async def update_existing_excursion(
    excursion_id: int,
    excursion: ExcursionUpdateScheme,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    """Update existing excursion."""
    try:
        return await service.update_excursion(
            excursion_id=excursion_id, excursion_update=excursion
        )
    except ExcursionNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@excursion_router.delete(
    "/excursions/{excursion_id}",
    responses={
        404: {"description": "Excursion not found"},
    },
)
async def delete_existing_excursion(
    excursion_id: int,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> dict:
    """Delete existing excursion."""
    try:
        await service.delete_excursion(excursion_id=excursion_id)
        return {"message": "Excursion deleted successfully"}
    except ExcursionNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@excursion_router.patch(
    "/excursions/{excursion_id}/toggle-active", response_model=ExcursionScheme
)
async def toggle_excursion_active(
    excursion_id: int,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    """Toggle excursion activity."""
    try:
        return await service.toggle_excursion_activity(excursion_id=excursion_id)
    except ExcursionNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@excursion_router.patch(
    "/excursions/{excursion_id}/add_people",
    response_model=ExcursionScheme,
    responses={
        400: {"description": "Add people overflow"},
        404: {"description": "Excursion not found"},
    },
)
async def add_people(
    excursion_id: int,
    people_count: int,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    """Add people to excursion."""
    try:
        return await service.change_people_left_count(
            excursion_id=excursion_id, count_people=people_count
        )
    except (
        ExcursionNotFoundError,
        ExcursionAddPeopleOverflowError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e


@excursion_router.put(
    "/excursions/{excursion_id}/bus-number",
    response_model=ExcursionScheme,
    responses={
        400: {"description": "Bus number can not be under zero"},
        404: {"description": "Excursion not found"},
    },
)
async def change_bus_number(
    excursion_id: int,
    bus_number: int,
    service: Annotated[ExcursionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    """Change bus number."""
    try:
        return await service.change_bus_number(
            excursion_id=excursion_id, bus_number=bus_number
        )
    except (
        ExcursionNotFoundError,
        ExcursionBusNumberNegativeError,
    ) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        ) from e
