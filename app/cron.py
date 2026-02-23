from typing import Callable

import aiocron
from loguru import logger

from app.booking.service import BookingService
from app.excursions.service import ExcurionService


class CronManager:
    def __init__(self) -> None:
        self._jobs: dict[Callable, aiocron.Cron] = {}

    def add_job(self, schedule: str, func: Callable) -> aiocron.Cron:
        job = aiocron.crontab(schedule, func=func)
        self._jobs[func] = job
        logger.debug(
            "Create new cron job with schedule={!r} and func={!r}", schedule, func
        )
        return job

    def stop_all(self) -> None:
        for func, job in self._jobs.items():
            job.stop()
            logger.debug("Cron job for func={!r} stopped.", func)


cron_manager = CronManager()


def deactivate_past_excurions_cron() -> None:
    service = ExcurionService()
    cron_manager.add_job("0 0 * * *", service.deactivate_past_excurions)


def deactivate_past_bookings() -> None:
    service = BookingService()
    cron_manager.add_job("15 0 * * *", service.deactivate_past_bookings)
