from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.auth.depends import require_superuser
from app.auth.schemas import UserSchema
from app.excursions.depends import get_excursion_service
from app.excursions.files import save_uploaded_file
from app.excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionDetailsCreateScheme,
    ExcursionDetailsScheme,
    ExcursionDetailsUpdateScheme,
    ExcursionFullScheme,
    ExcursionScheme,
    ExcursionUpdateScheme,
)
from app.excursions.service import ExcurionService

excursion_router = APIRouter(tags=["Excursion"])


# ===== Public ручки для работы с ExcursionModel =====
@excursion_router.get("/excursions", response_model=list[ExcursionScheme])
async def read_excursions(
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    skip: int = 0,
    limit: int = 100,
    category: str | None = Query(None),
) -> list[ExcursionScheme]:
    return await service.get_excursions(
        offset=skip,
        limit=limit,
        category=category,
    )


@excursion_router.get("/excursions/{excursion_id}", response_model=ExcursionScheme)
async def read_excursion(
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    excursion_id: int,
) -> ExcursionScheme:
    return await service.get_excursion(excursion_id=excursion_id)


@excursion_router.get("/excursions/search/", response_model=list[ExcursionScheme])
async def search_excursions_by_term(
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    q: str = Query(...),
) -> list[ExcursionScheme]:
    return await service.search_excursions(search_term=q)


@excursion_router.get(
    "/excursions/category/{category}", response_model=list[ExcursionScheme]
)
async def read_excursions_by_category(
    category: str,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
) -> list[ExcursionScheme]:
    return await service.get_excursions(
        category=category,
    )


# ===== Admin ручки для работы с ExcursionModel =====
@excursion_router.post("/excursions", response_model=ExcursionScheme)
async def create_new_excursion(
    excursion: ExcursionCreateScheme,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    new_excursion = await service.create_excursion(excursion=excursion)
    return new_excursion


@excursion_router.put("/excursions/{excursion_id}", response_model=ExcursionScheme)
async def update_existing_excursion(
    excursion_id: int,
    excursion: ExcursionUpdateScheme,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    return await service.update_excursion(
        excursion_id=excursion_id, excursion_update=excursion
    )


@excursion_router.delete("/excursions/{excursion_id}")
async def delete_existing_excursion(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> dict:
    await service.delete_excursion(excursion_id=excursion_id)
    return {"message": "Excursion deleted successfully"}


@excursion_router.patch(
    "/excursions/{excursion_id}/toggle-active", response_model=ExcursionScheme
)
async def toggle_excursion_active(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    return await service.toggle_excursion_activity(excursion_id=excursion_id)


@excursion_router.patch("/excursions/{excursion_id}/add_people")
async def add_people(
    excursion_id: int,
    people_count: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    return await service.add_people_left(
        excursion_id=excursion_id, count_people=people_count
    )


@excursion_router.put("/excursions/{excursion_id}/bus-number")
async def change_bus_number(
    excursion_id: int,
    bus_number: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionScheme:
    return await service.change_bus_number_crud(
        excursion_id=excursion_id, bus_number=bus_number
    )


@excursion_router.post("/excursions/save_image")
async def save_image(
    image_file: Annotated[UploadFile, File(...)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> str:
    try:
        return save_uploaded_file(image_file)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при сохранении изображения: {str(e)}"
        ) from Exception


# ===== Public ручки для работы с ExcursionDetailsModel =====
@excursion_router.get("/excursions/{excursion_id}/details")
async def get_excursion_details_route(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
) -> ExcursionDetailsScheme:
    return await service.get_excursion_details(excursion_id=excursion_id)


@excursion_router.get("/excursions/{excursion_id}/full")
async def get_excursion_full(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
) -> ExcursionFullScheme:
    return await service.get_excursion_full_info(excursion_id=excursion_id)


# ===== Admin ручки для работы с ExcursionDetailsModel =====
@excursion_router.post("/excursions/{excursion_id}/details")
async def create_excursion_details_route(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    details: ExcursionDetailsCreateScheme,
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionDetailsScheme:
    return await service.create_excursion_details(
        excursion_id=excursion_id, details=details
    )


@excursion_router.put("/excursions/{excursion_id}/details")
async def update_excursion_details_route(
    excursion_id: int,
    details: ExcursionDetailsUpdateScheme,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ExcursionDetailsScheme:
    return await service.update_excursion_details(
        excursion_id=excursion_id, details_update=details
    )


@excursion_router.delete("/excursions/{excursion_id}/details")
async def delete_excursion_details_route(
    excursion_id: int,
    service: Annotated[ExcurionService, Depends(get_excursion_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> dict:
    await service.delete_excursion_details(excursion_id=excursion_id)
    return {"message": "Excursion details deleted successfully"}
