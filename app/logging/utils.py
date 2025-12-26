import logging

from loguru import logger

from app.logging.handlers import (
    InterceptHandler,
    add_console_handler,
    add_error_handler,
    add_file_handler,
    add_http_handler,
)


def setup_new_logger() -> None:
    add_console_handler()
    add_file_handler()
    add_error_handler()
    add_http_handler()
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)


def remove_all_logers() -> None:
    remove_logging_handlers()
    remove_loguru_handlers()
    remove_fastapi_handlers()


def remove_logging_handlers() -> None:
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


def remove_loguru_handlers() -> None:
    # Удаляем стандартный обработчик Loguru
    logger.remove()


def remove_fastapi_handlers() -> None:
    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "asyncio",
        "starlette",
    )

    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = []
        logging_logger.propagate = True
