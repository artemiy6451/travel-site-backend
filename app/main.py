import sys
from contextlib import asynccontextmanager
from typing import Any

from auth.router import login_router
from cache import redis_client
from config import settings
from excursions.router import excursion_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Проверяем подключение к Redis при запуске"""
    try:
        redis_client.ping()
    except Exception:
        sys.exit(1)

    yield
    redis_client.close()


app = FastAPI(
    lifespan=lifespan,
    title="Travelvv API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
)

app.include_router(login_router)
app.include_router(excursion_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")
