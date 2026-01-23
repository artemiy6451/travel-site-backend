import statistics

from fastapi import HTTPException
from sqlalchemy import and_

from app.cache import cached, invalidate_cache
from app.config import settings
from app.database import async_session_maker
from app.repository import SQLAlchemyRepository
from app.reviews.models import ReviewModel
from app.reviews.schemas import ReviewCreate, ReviewSchema


class ReviewService:
    def __init__(self) -> None:
        self.repository: SQLAlchemyRepository[ReviewModel] = SQLAlchemyRepository(
            async_session_maker, ReviewModel
        )

    @cached(ttl=settings.ttl, key_prefix="one_review")
    async def get_review(self, review_id: int) -> ReviewSchema:
        review = await self.repository.find_one(filter=ReviewModel.id == review_id)
        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")

        return review.to_read_model()

    async def create_review(self, review: ReviewCreate) -> ReviewSchema:
        created_review = await self.repository.add_one(review.model_dump())
        return created_review.to_read_model()

    @cached(ttl=settings.ttl, key_prefix="approved_reviews")
    async def get_approved_reviews(self) -> list[ReviewSchema]:
        filter = and_(ReviewModel.is_active)
        reviews = await self.repository.find_all(filter_by=filter)

        return [review.to_read_model() for review in reviews]

    @cached(ttl=settings.ttl, key_prefix="pending_reviews")
    async def get_pending_reviews(self) -> list[ReviewSchema]:
        filter = ReviewModel.is_active == False  # noqa: E712
        reviews = await self.repository.find_all(filter_by=filter)

        return [review.to_read_model() for review in reviews]

    @cached(ttl=settings.ttl, key_prefix="all_reviews")
    async def get_all_reviews(self) -> list[ReviewSchema]:
        reviews = await self.repository.find_all()
        return [review.to_read_model() for review in reviews]

    @invalidate_cache(
        "one_review*",
        "approved_reviews*",
        "pending_reviews*",
        "all_reviews*",
        "review_stats*",
    )
    async def toggle_show_review(self, review_id: int) -> ReviewSchema:
        review = await self.get_review(review_id)

        data = {"is_active": not review.is_active}

        new_review = await self.repository.update_one(id=review_id, data=data)
        return new_review.to_read_model()

    @invalidate_cache(
        "one_review*",
        "approved_reviews*",
        "pending_reviews*",
        "all_reviews*",
        "review_stats*",
    )
    async def delete_review(self, review_id: int) -> bool:
        await self.get_review(review_id)
        await self.repository.delete_one(id=review_id)
        return True

    @cached(settings.ttl, "review_stats")
    async def get_reviews_stats(self) -> dict:
        reviews = await self.get_approved_reviews()

        total = len(reviews)
        if total == 0:
            return {"total": 0, "average_rating": 0}

        try:
            avg = statistics.mean([review.rating for review in reviews])
        except AttributeError:
            avg = statistics.mean([review["rating"] for review in reviews])

        return {
            "total": total,
            "average_rating": round(float(avg), 2) if avg else 0,
        }

    def __repr__(self) -> str:
        return "ReviewService"
