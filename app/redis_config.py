import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import redis
from fastapi import FastAPI


class RedisConfig:
    def __init__(self) -> None:
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.decode_responses = True


def get_redis_connection() -> redis.Redis:
    config = RedisConfig()
    return redis.Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        decode_responses=config.decode_responses,
        socket_connect_timeout=5,
        retry_on_timeout=True,
    )


redis_client = get_redis_connection()


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    try:
        redis_client.ping()
    except Exception:
        sys.exit(1)

    yield
    redis_client.close()
