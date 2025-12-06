from app.excursions.service import ExcurionService


async def get_excursion_service() -> ExcurionService:
    return ExcurionService()
