import aiocron
from loguru import logger

from app.excursions.service import ExcurionService


@aiocron.crontab("0 0 * * *")
async def deactivate_past_excurions_cron() -> None:
    logger.info("Run cron deactivate past excursions")
    service = ExcurionService()
    await service.deactivate_past_excurions()
