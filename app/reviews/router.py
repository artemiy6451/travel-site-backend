from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.depends import require_superuser
from app.auth.schemas import UserSchema
from app.reviews.depends import get_review_service
from app.reviews.schemas import ReviewCreate, ReviewSchema
from app.reviews.service import ReviewService

router = APIRouter(prefix="/review", tags=["Reviews"])


@router.get("/")
async def get_approved_reviews(
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> list[ReviewSchema]:
    return await service.get_approved_reviews()


@router.get("/stats")
async def get_reviews_stats(
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> dict:
    return await service.get_reviews_stats()


@router.post("/")
async def create_review(
    review: ReviewCreate,
    service: Annotated[ReviewService, Depends(get_review_service)],
) -> ReviewSchema:
    return await service.create_review(review)


# Admin endpoints
@router.get("/admin/all")
async def get_all_reviews(
    service: Annotated[ReviewService, Depends(get_review_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[ReviewSchema]:
    return await service.get_all_reviews()


@router.get("/admin/pending")
async def get_pending_reviews(
    service: Annotated[ReviewService, Depends(get_review_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> list[ReviewSchema]:
    return await service.get_pending_reviews()


@router.post("/admin/{review_id}/toggle")
async def approve_review(
    review_id: int,
    service: Annotated[ReviewService, Depends(get_review_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> ReviewSchema:
    db_review = await service.toggle_show_review(review_id)
    return db_review


@router.delete("/admin/{review_id}")
async def delete_review_admin(
    review_id: int,
    service: Annotated[ReviewService, Depends(get_review_service)],
    _: Annotated[UserSchema, Depends(require_superuser)],
) -> dict:
    await service.delete_review(review_id)
    return {"message": "Review deleted"}
