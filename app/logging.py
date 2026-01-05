import logging
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)


def add_console_handler() -> None:
    logger.add(
        sys.stdout,
        format=CONSOLE_FORMAT,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


def add_file_handler() -> None:
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        serialize=True,
    )


def add_error_handler() -> None:
    logger.add(
        LOG_DIR / "errors_{time:YYYY-MM-DD}.log",
        format=FILE_FORMAT,
        level="WARNING",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        enqueue=True,
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


def setup_new_logger() -> None:
    logger.remove()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=logging.DEBUG,
        force=True,
    )

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "starlette",
        "asyncio",
    ):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    add_console_handler()
    add_file_handler()
    add_error_handler()
