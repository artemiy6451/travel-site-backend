import asyncio
from functools import wraps
from typing import Callable

from loguru import logger


def retry(max_attempts: int = 10, delay: int = 60) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: list, **kwargs: dict) -> BaseException | None:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
                        break

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed "
                        f"for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    await asyncio.sleep(current_delay)

            # Если все попытки исчерпаны, логируем и выбрасываем последнее исключение
            if isinstance(last_exception, BaseException):
                raise last_exception
            else:
                raise Exception("Max retry attempt.")

        return wrapper

    return decorator
