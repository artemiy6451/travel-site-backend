"""Depends for excursions module."""

from app.excursions.service import ExcursionService


async def get_excursion_service() -> ExcursionService:
    """Get excursions service."""
    return ExcursionService()
