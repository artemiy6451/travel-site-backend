from typing import Sequence

from auth.depends import require_superuser
from auth.models import User
from database import get_db
from excursions.crud import (
    add_people_left,
    change_bus_number_crud,
    create_excursion,
    create_excursion_details,
    create_or_update_excursion_details,
    delete_excursion,
    delete_excursion_details,
    get_excursion,
    get_excursion_details,
    get_excursion_full_info,
    get_excursions,
    get_excursions_by_category,
    search_excursions,
    toggle_excursion_activity,
    update_excursion,
    update_excursion_details,
)
from excursions.files import save_uploaded_file
from excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionDetailsCreateScheme,
    ExcursionDetailsScheme,
    ExcursionDetailsUpdateScheme,
    ExcursionFullScheme,
    ExcursionScheme,
    ExcursionUpdateScheme,
)
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

excursion_router = APIRouter(tags=["Excursion API"])


@excursion_router.get("/excursions", response_model=Sequence[ExcursionScheme])
def read_excursions(
    skip: int = 0,
    limit: int = 100,
    category: str | None = Query(None, description="Фильтр по категории"),
    min_price: int | None = Query(None, description="Минимальная цена"),
    max_price: int | None = Query(None, description="Максимальная цена"),
    db: Session = Depends(get_db),
) -> Sequence[ExcursionScheme]:
    """
    Получить список экскурсий с возможностью фильтрации
    """
    excursions = get_excursions(
        db,
        skip=skip,
        limit=limit,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )
    return excursions


@excursion_router.get("/excursions/{excursion_id}", response_model=ExcursionScheme)
def read_excursion(excursion_id: int, db: Session = Depends(get_db)) -> ExcursionScheme:
    """
    Получить экскурсию по ID
    """
    db_excursion = get_excursion(db, excursion_id=excursion_id)
    if db_excursion is None:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return db_excursion


@excursion_router.post("/excursions", response_model=ExcursionScheme)
def create_new_excursion(
    excursion: ExcursionCreateScheme,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionScheme:
    """
    Создать новую экскурсию (требуется авторизация)
    """
    return create_excursion(db=db, excursion=excursion)


@excursion_router.put("/excursions/{excursion_id}", response_model=ExcursionScheme)
def update_existing_excursion(
    excursion_id: int,
    excursion: ExcursionUpdateScheme,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionScheme:
    """
    Обновить экскурсию (требуется авторизация)
    """
    db_excursion = update_excursion(
        db, excursion_id=excursion_id, excursion_update=excursion
    )
    if db_excursion is None:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return db_excursion


@excursion_router.delete("/excursions/{excursion_id}")
def delete_existing_excursion(
    excursion_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> dict:
    """
    Удалить экскурсию (требуется авторизация)
    """
    success = delete_excursion(db, excursion_id=excursion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return {"message": "Excursion deleted successfully"}


@excursion_router.get(
    "/excursions/category/{category}", response_model=Sequence[ExcursionScheme]
)
def read_excursions_by_category(
    category: str, db: Session = Depends(get_db)
) -> Sequence[ExcursionScheme]:
    """
    Получить экскурсии по категории
    """
    excursions = get_excursions_by_category(db, category=category)
    return excursions


@excursion_router.get("/excursions/search/", response_model=Sequence[ExcursionScheme])
def search_excursions_by_term(
    q: str = Query(..., description="Поисковый запрос"), db: Session = Depends(get_db)
) -> Sequence[ExcursionScheme]:
    """
    Поиск экскурсий по названию и описанию
    """
    excursions = search_excursions(db, search_term=q)
    return excursions


@excursion_router.patch(
    "/excursions/{excursion_id}/toggle-active", response_model=ExcursionScheme
)
def toggle_excursion_active(
    excursion_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionScheme:
    """
    Переключить статус активности экскурсии
    """
    db_excursion = toggle_excursion_activity(db, excursion_id=excursion_id)
    if db_excursion is None:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return db_excursion


@excursion_router.patch("/excursions/{excursion_id}/add_people")
def add_people(
    excursion_id: int,
    people_count: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionCreateScheme:
    """
    Добавить определенное количество человек на маршрут
    """
    db_excursion = add_people_left(
        db, excursion_id=excursion_id, count_people=people_count
    )
    if db_excursion is None:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return db_excursion


@excursion_router.get(
    "/excursions/{excursion_id}/full",
    response_model=ExcursionFullScheme,
    summary="Полная информация об экскурсии",
    description="Получить полную информацию об экскурсии включая детали маршрута, включения и программу",
)
def get_excursion_full(
    excursion_id: int, db: Session = Depends(get_db)
) -> ExcursionFullScheme:
    """
    Получить полную информацию об экскурсии (основная информация + детали)
    """
    full_info = get_excursion_full_info(db, excursion_id=excursion_id)
    return full_info


@excursion_router.get(
    "/excursions/{excursion_id}/details",
    response_model=ExcursionDetailsScheme,
    summary="Детальная информация об экскурсии",
    description="Получить детальную информацию об экскурсии (описание маршрута, включения, программа)",
)
def get_excursion_details_route(
    excursion_id: int, db: Session = Depends(get_db)
) -> ExcursionDetailsScheme:
    """
    Получить детальную информацию об экскурсии
    """
    db_details = get_excursion_details(db, excursion_id=excursion_id)
    if db_details is None:
        raise HTTPException(status_code=404, detail="Excursion details not found")
    return db_details


@excursion_router.post(
    "/excursions/{excursion_id}/details",
    response_model=ExcursionDetailsScheme,
    summary="Создать детальную информацию",
    description="Создать детальную информацию для экскурсии (требуется авторизация администратора)",
)
def create_excursion_details_route(
    excursion_id: int,
    details: ExcursionDetailsCreateScheme,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionDetailsScheme:
    """
    Создать детальную информацию для экскурсии
    """
    return create_excursion_details(db, excursion_id=excursion_id, details=details)


@excursion_router.put(
    "/excursions/{excursion_id}/details",
    response_model=ExcursionDetailsScheme,
    summary="Обновить детальную информацию",
    description="Обновить детальную информацию об экскурсии (требуется авторизация администратора)",
)
def update_excursion_details_route(
    excursion_id: int,
    details: ExcursionDetailsUpdateScheme,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionDetailsScheme:
    """
    Обновить детальную информацию об экскурсии
    """
    db_details = update_excursion_details(
        db, excursion_id=excursion_id, details_update=details
    )
    if db_details is None:
        raise HTTPException(status_code=404, detail="Excursion details not found")
    return db_details


@excursion_router.patch(
    "/excursions/{excursion_id}/details",
    response_model=ExcursionDetailsScheme,
    summary="Создать или обновить детальную информацию",
    description="Создать или обновить детальную информацию об экскурсии (требуется авторизация администратора)",
)
def create_or_update_excursion_details_route(
    excursion_id: int,
    details: ExcursionDetailsCreateScheme,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionDetailsScheme:
    """
    Создать или обновить детальную информацию об экскурсии
    """
    return create_or_update_excursion_details(
        db, excursion_id=excursion_id, details=details
    )


@excursion_router.delete(
    "/excursions/{excursion_id}/details",
    summary="Удалить детальную информацию",
    description="Удалить детальную информацию об экскурсии (требуется авторизация администратора)",
)
def delete_excursion_details_route(
    excursion_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> dict:
    """
    Удалить детальную информацию об экскурсии
    """
    success = delete_excursion_details(db, excursion_id=excursion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Excursion details not found")
    return {"message": "Excursion details deleted successfully"}


# ===== Ручки для работы с отдельными блоками детальной информации =====


@excursion_router.get(
    "/excursions/{excursion_id}/inclusions",
    summary="Что входит в экскурсию",
    description="Получить список того, что входит в экскурсию",
)
def get_excursion_inclusions(
    excursion_id: int,
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Получить список включений экскурсии
    """
    db_details = get_excursion_details(db, excursion_id=excursion_id)
    if db_details is None or db_details.inclusions is None:
        return []
    return db_details.inclusions


@excursion_router.get(
    "/excursions/{excursion_id}/itinerary",
    summary="Программа тура",
    description="Получить пошаговую программу тура",
)
def get_excursion_itinerary(
    excursion_id: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Получить программу тура
    """
    db_details = get_excursion_details(db, excursion_id=excursion_id)
    if db_details is None or db_details.itinerary is None:
        return []
    return db_details.itinerary


@excursion_router.get(
    "/excursions/{excursion_id}/requirements",
    summary="Требования к участникам",
    description="Получить список требований к участникам экскурсии",
)
def get_excursion_requirements(
    excursion_id: int,
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Получить требования к участникам
    """
    db_details = get_excursion_details(db, excursion_id=excursion_id)
    if db_details is None or db_details.requirements is None:
        return []
    return db_details.requirements


@excursion_router.post(
    "/excursions/save_image",
    summary="Сохранение картинки",
    description="Сохранение картинки и возвращение url",
    response_description="URL сохраненного изображения",
)
async def save_image(
    image_file: UploadFile = File(..., description="Файл изображения для загрузки"),
    _: User = Depends(require_superuser),
) -> str:
    """
    Сохраняет загруженное изображение и возвращает его URL

    - **image_file**: Файл изображения (поддерживаемые форматы: jpg, jpeg, png, webp)
    """
    try:
        # Используем существующую функцию для сохранения файла
        image_url = save_uploaded_file(image_file)
        return image_url

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при сохранении изображения: {str(e)}"
        ) from Exception


@excursion_router.put(
    "/excursions/{excursion_id}/bus-number",
    response_model=ExcursionScheme,
    status_code=status.HTTP_200_OK,
    summary="Изменить номер автобуса экскурсии",
    description="Обновляет номер автобуса для указанной экскурсии",
)
async def change_bus_number(
    excursion_id: int,
    bus_number: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
) -> ExcursionScheme:
    try:
        updated_bus_number = change_bus_number_crud(
            db=db, excursion_id=excursion_id, bus_number=bus_number
        )
        return updated_bus_number
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обновление номера автобуса: {str(e)}"
        ) from Exception
