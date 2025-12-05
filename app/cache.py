import hashlib
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

from app.redis_config import redis_client

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для обработки datetime и других типов"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class RedisCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            serialized_value = json.dumps(value, cls=JSONEncoder, ensure_ascii=False)
            return bool(self.redis.setex(key, ttl, serialized_value))
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False


# Глобальный экземпляр кеша
redis_cache = RedisCache(redis_client)


def cached(ttl: int = 300, key_prefix: str = "", unless: Callable = None) -> Callable:
    """
    Декоратор для кеширования результатов функций в Redis
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Пропускаем кеширование если unless возвращает True
            if unless and unless(*args, **kwargs):
                return func(*args, **kwargs)

            # Создаем ключ кеша
            cache_key = _generate_cache_key(func.__name__, key_prefix, args, kwargs)

            # Пробуем получить из кеша
            cached_result = redis_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Выполняем функцию и кешируем результат
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)

            # Сериализуем результат перед сохранением в кеш
            serializable_result = _convert_to_serializable(result)
            redis_cache.set(cache_key, serializable_result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> Callable:
    """
    Декоратор для инвалидации кеша после выполнения функции
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            # Инвалидируем кеш после выполнения
            deleted_count = redis_cache.delete_pattern(pattern)
            logger.debug(
                f"Invalidated cache pattern {pattern}, deleted {deleted_count} keys"
            )
            return result

        return wrapper

    return decorator


def _generate_cache_key(func_name: str, prefix: str, args: tuple, kwargs: dict) -> str:
    """Генерация уникального ключа кеша"""
    key_parts = [prefix, func_name] if prefix else [func_name]

    # Добавляем аргументы
    if args:
        key_parts.append(str(args))
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))

    # Создаем хеш для длинных ключей
    key_string = ":".join(key_parts)
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return (
            f"{prefix}:{func_name}:{key_hash}" if prefix else f"{func_name}:{key_hash}"
        )

    return key_string.replace(" ", "")


def _convert_to_serializable(obj: Any) -> Any:
    """Рекурсивно преобразует объекты в сериализуемые структуры"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_serializable(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        # Для SQLAlchemy моделей и других объектов
        return _convert_to_serializable(obj.__dict__)
    else:
        return str(obj)
