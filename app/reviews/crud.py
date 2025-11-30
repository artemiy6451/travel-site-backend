from typing import List, Optional

from reviews.models import Review
from reviews.schemas import ReviewCreate, ReviewUpdate
from sqlalchemy import and_, func
from sqlalchemy.orm import Session


class ReviewCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_review(self, review: ReviewCreate) -> Review:
        db_review = Review(
            excursion_id=review.excursion_id,
            author_name=review.author_name,
            email=review.email,
            rating=review.rating,
            text=review.text,
        )
        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def get_review(self, review_id: int) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_approved_reviews(
        self, skip: int = 0, limit: int = 100, excursion_id: Optional[int] = None
    ) -> List[Review]:
        query = self.db.query(Review).filter(
            and_(Review.is_approved, Review.is_active)
        )

        if excursion_id:
            query = query.filter(Review.excursion_id == excursion_id)

        return query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

    def get_pending_reviews(self, skip: int = 0, limit: int = 100) -> List[Review]:
        return (
            self.db.query(Review)
            .filter(Review.is_approved)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_reviews(self, skip: int = 0, limit: int = 100) -> List[Review]:
        return (
            self.db.query(Review)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_review(
        self, review_id: int, review_update: ReviewUpdate
    ) -> Optional[Review]:
        db_review = self.get_review(review_id)
        if not db_review:
            return None

        update_data = review_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_review, field, value)

        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def approve_review(self, review_id: int) -> Optional[Review]:
        db_review = self.get_review(review_id)
        if not db_review:
            return None

        db_review.is_approved = True
        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def hide_review(self, review_id: int) -> Optional[Review]:
        db_review = self.get_review(review_id)
        if not db_review:
            return None

        db_review.is_active = False
        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def show_review(self, review_id: int) -> Optional[Review]:
        db_review = self.get_review(review_id)
        if not db_review:
            return None

        db_review.is_active = True
        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def delete_review(self, review_id: int) -> bool:
        db_review = self.get_review(review_id)
        if not db_review:
            return False

        self.db.delete(db_review)
        self.db.commit()
        return True

    def get_reviews_stats(self, excursion_id: Optional[int] = None) -> dict:
        query = self.db.query(Review).filter(
            and_(Review.is_approved, Review.is_active)
        )

        if excursion_id:
            query = query.filter(Review.excursion_id == excursion_id)

        total = query.count()
        if total == 0:
            return {"total": 0, "average_rating": 0}

        avg_rating = (
            self.db.query(func.avg(Review.rating))
            .filter(and_(Review.is_approved, Review.is_active))
            .scalar()
        )

        return {
            "total": total,
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
        }
