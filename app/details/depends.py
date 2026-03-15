from app.details.service import DetailsService


async def get_details_service() -> DetailsService:
    """Get excursions service."""
    return DetailsService()
