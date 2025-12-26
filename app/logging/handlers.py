import logging
import sys
from pathlib import Path

from loguru import logger

from app.config import settings
from app.logging.formats import CONSOLE_FORMAT, FILE_FORMAT

# Создаем директории для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def add_console_handler() -> None:
    # Добавляем обработчик для консоли
    logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level="DEBUG" if settings.mode == "development" else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


def add_file_handler() -> None:
    # Добавляем обработчик для файла (ротация по размеру и времени)
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="DEBUG",
        rotation="10 MB",  # Ротация при достижении 10MB
        retention="30 days",  # Храним логи 30 дней
        compression="zip",  # Сжимаем старые логи
        enqueue=True,  # Асинхронная запись
        backtrace=True,
        diagnose=True,
        serialize=True,
    )


def add_error_handler() -> None:
    # Добавляем обработчик для ошибок (отдельный файл)
    logger.add(
        LOG_DIR / "errors_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="WARNING",
        rotation="10 MB",
        retention="90 days",  # Ошибки храним дольше
        compression="zip",
        enqueue=True,
        serialize=True,
    )


def add_http_handler() -> None:
    # Добавляем обработчик для HTTP запросов (отдельный файл)
    logger.add(
        LOG_DIR / "http_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        filter=lambda record: "http" in record["extra"].get("context", ""),
        serialize=True,
    )


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2

        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
