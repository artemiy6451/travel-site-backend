from cache import cached, invalidate_cache
from excursions.models import Excursion, ExcursionDetails
from excursions.schemas import (
    ExcursionCreateScheme,
    ExcursionDetailsCreateScheme,
    ExcursionDetailsUpdateScheme,
    ExcursionScheme,
    ExcursionUpdateScheme,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload


# GET запросы с кешированием
@cached(ttl=300, key_prefix="excursions")
def get_excursions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
) -> list[Excursion]:
    query = db.query(Excursion)

    # Фильтры
    if category:
        query = query.filter(Excursion.category == category)
    if min_price is not None:
        query = query.filter(Excursion.price >= min_price)
    if max_price is not None:
        query = query.filter(Excursion.price <= max_price)

    return query.offset(skip).limit(limit).all()


@cached(ttl=300, key_prefix="excursion")
def get_excursion(db: Session, excursion_id: int) -> Excursion | None:
    excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    return excursion


@cached(ttl=300, key_prefix="excursions_category")
def get_excursions_by_category(db: Session, category: str) -> list[Excursion]:
    return db.query(Excursion).filter(Excursion.category == category).all()


@cached(ttl=300, key_prefix="excursions_search")
def search_excursions(db: Session, search_term: str) -> list[Excursion]:
    return (
        db.query(Excursion)
        .filter(
            Excursion.title.ilike(f"%{search_term}%")
            | Excursion.description.ilike(f"%{search_term}%")
        )
        .all()
    )


@cached(ttl=300, key_prefix="excursion_details")
def get_excursion_details(db: Session, excursion_id: int) -> ExcursionDetails | None:
    """Получить детальную информацию об экскурсии"""
    return (
        db.query(ExcursionDetails)
        .filter(ExcursionDetails.excursion_id == excursion_id)
        .first()
    )


@cached(ttl=300, key_prefix="excursion_with_details")
def get_excursion_with_details(db: Session, excursion_id: int) -> Excursion | None:
    """Получить экскурсию вместе с детальной информацией"""
    return (
        db.query(Excursion)
        .options(joinedload(Excursion.details))
        .filter(Excursion.id == excursion_id)
        .first()
    )


@cached(ttl=300, key_prefix="excursion_full")
def get_excursion_full_info(db: Session, excursion_id: int) -> dict:
    """Получить полную информацию об экскурсии (основная + детальная)"""
    excursion = get_excursion_with_details(db, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")

    result = {
        "id": excursion.id,
        "title": excursion.title,
        "category": excursion.category,
        "description": excursion.description,
        "date": excursion.date,
        "price": excursion.price,
        "duration": excursion.duration,
        "people_amount": excursion.people_amount,
        "people_left": excursion.people_left,
        "is_active": excursion.is_active,
        "image_url": excursion.image_url,
        "details": None,
    }

    # Добавляем детальную информацию, если она есть
    if excursion.details:
        result["details"] = {
            "id": excursion.details.id,
            "excursion_id": excursion.details.excursion_id,
            "description": excursion.details.description,
            "inclusions": excursion.details.inclusions,
            "itinerary": excursion.details.itinerary,
            "meeting_point": excursion.details.meeting_point,
            "requirements": excursion.details.requirements,
            "recommendations": excursion.details.recommendations,
        }

    return result


# POST/PUT/DELETE запросы с инвалидацией кеша
@invalidate_cache("excursions*")
@invalidate_cache("excursion*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_with_details*")
def create_excursion(db: Session, excursion: ExcursionCreateScheme) -> Excursion:
    db_excursion = Excursion(
        title=excursion.title,
        category=excursion.category,
        description=excursion.description,
        price=excursion.price,
        duration=excursion.duration,
        date=excursion.date,
        people_amount=excursion.people_amount,
        people_left=excursion.people_left,
        is_active=excursion.is_active,
        image_url=excursion.image_url,
    )
    db.add(db_excursion)
    db.commit()
    db.refresh(db_excursion)
    return db_excursion


@invalidate_cache("excursions*")
@invalidate_cache("excursion*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_with_details*")
def update_excursion(
    db: Session, excursion_id: int, excursion_update: ExcursionUpdateScheme
) -> Excursion | None:
    db_excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    if db_excursion:
        update_data = excursion_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_excursion, field, value)
        db.commit()
        db.refresh(db_excursion)
    return db_excursion


@invalidate_cache("excursions*")
@invalidate_cache("excursion*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_with_details*")
def delete_excursion(db: Session, excursion_id: int) -> bool:
    db_excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    if db_excursion:
        db.delete(db_excursion)
        db.commit()
        return True
    return False


@invalidate_cache("excursions*")
@invalidate_cache("excursion*")
@invalidate_cache("excursion_full*")
def toggle_excursion_activity(db: Session, excursion_id: int) -> Excursion | None:
    db_excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    if db_excursion:
        db_excursion.is_active = not db_excursion.is_active
        db.commit()
        db.refresh(db_excursion)
    return db_excursion


@invalidate_cache("excursions*")
@invalidate_cache("excursion*")
@invalidate_cache("excursion_full*")
def add_people_left(
    db: Session, excursion_id: int, count_people: int
) -> Excursion | None:
    db_excursion = db.query(Excursion).filter(Excursion.id == excursion_id).first()
    if db_excursion:
        left = db_excursion.people_left - count_people
        if left < 0:
            raise HTTPException(
                status_code=405, detail=f"Can not add {count_people} people, owerflow."
            )
        db_excursion.people_left = left
        db.commit()
        db.refresh(db_excursion)
    return db_excursion


@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_with_details*")
def create_excursion_details(
    db: Session, excursion_id: int, details: ExcursionDetailsCreateScheme
) -> ExcursionDetails:
    """Создать детальную информацию для экскурсии"""

    # Проверяем, существует ли экскурсия
    excursion = get_excursion(db, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")

    # Проверяем, не созданы ли уже детали для этой экскурсии
    existing_details = get_excursion_details(db, excursion_id)
    if existing_details:
        raise HTTPException(status_code=400, detail="Excursion details already exist")

    db_details = ExcursionDetails(excursion_id=excursion_id, **details.model_dump())
    db.add(db_details)
    db.commit()
    db.refresh(db_details)
    return db_details


@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_with_details*")
def update_excursion_details(
    db: Session, excursion_id: int, details_update: ExcursionDetailsUpdateScheme
) -> ExcursionDetails | None:
    """Обновить детальную информацию об экскурсии"""
    db_details = get_excursion_details(db, excursion_id)
    if db_details:
        update_data = details_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_details, field, value)
        db.commit()
        db.refresh(db_details)
    return db_details


@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_with_details*")
def delete_excursion_details(db: Session, excursion_id: int) -> bool:
    """Удалить детальную информацию об экскурсии"""
    db_details = get_excursion_details(db, excursion_id)
    if db_details:
        db.delete(db_details)
        db.commit()
        return True
    return False


@invalidate_cache("excursion_details*")
@invalidate_cache("excursion_full*")
@invalidate_cache("excursion_with_details*")
def create_or_update_excursion_details(
    db: Session, excursion_id: int, details: ExcursionDetailsCreateScheme
) -> ExcursionDetails:
    """Создать или обновить детальную информацию об экскурсии"""
    existing_details = get_excursion_details(db, excursion_id)

    if existing_details:
        # Обновляем существующую запись
        update_data = details.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_details, field, value)
        db.commit()
        db.refresh(existing_details)
        return existing_details
    else:
        # Создаем новую запись
        return create_excursion_details(db, excursion_id, details)
