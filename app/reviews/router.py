from typing import List, Optional

from auth.depends import require_superuser
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from reviews import crud, schemas
from sqlalchemy.orm import Session

router = APIRouter(prefix="/review", tags=["reviews"])


# Public endpoints
@router.get("/", response_model=List[schemas.ReviewPublic])
async def get_approved_reviews(
    skip: int = 0,
    limit: int = 100,
    excursion_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Получить одобренные отзывы"""
    review_crud = crud.ReviewCRUD(db)
    return review_crud.get_approved_reviews(skip, limit, excursion_id)


@router.get("/stats")
async def get_reviews_stats(
    excursion_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """Получить статистику по отзывам"""
    review_crud = crud.ReviewCRUD(db)
    return review_crud.get_reviews_stats(excursion_id)


@router.post("/", response_model=schemas.ReviewPublic)
async def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """Создать новый отзыв (доступно всем)"""
    review_crud = crud.ReviewCRUD(db)
    return review_crud.create_review(review)


# Admin endpoints
@router.get("/admin/all", response_model=List[schemas.ReviewAdmin])
async def get_all_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Получить все отзывы (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    return review_crud.get_all_reviews(skip, limit)


@router.get("/admin/pending", response_model=List[schemas.ReviewAdmin])
async def get_pending_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Получить отзывы на модерации (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    return review_crud.get_pending_reviews(skip, limit)


@router.post("/admin/{review_id}/approve", response_model=schemas.ReviewAdmin)
async def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Одобрить отзыв (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    db_review = review_crud.approve_review(review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return db_review


@router.post("/admin/{review_id}/hide", response_model=schemas.ReviewAdmin)
async def hide_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Скрыть отзыв (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    db_review = review_crud.hide_review(review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return db_review


@router.post("/admin/{review_id}/show", response_model=schemas.ReviewAdmin)
async def show_review(
    review_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Показать скрытый отзыв (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    db_review = review_crud.show_review(review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return db_review


@router.delete("/admin/{review_id}")
async def delete_review_admin(
    review_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_superuser),
):
    """Удалить отзыв (только для админа)"""
    review_crud = crud.ReviewCRUD(db)
    success = review_crud.delete_review(review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return {"message": "Отзыв удален"}
