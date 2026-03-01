from app.excursions.service import ExcursionService


async def get_excursion_service() -> ExcursionService:
    return ExcursionService()
