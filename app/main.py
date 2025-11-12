import sys
from contextlib import asynccontextmanager
from typing import Any

from auth.router import login_router
from cache import redis_client
from excursions.router import excursion_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Проверяем подключение к Redis при запуске"""
    try:
        redis_client.ping()
    except Exception:
        sys.exit(1)

    yield
    redis_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(login_router)
app.include_router(excursion_router)

# Альтернативно - разрешить все origins (только для разработки!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
