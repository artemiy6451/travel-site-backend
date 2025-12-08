import locale
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import login_router
from app.booking.router import booking_router
from app.config import settings
from app.excursions.router import excursion_router
from app.redis_config import redis_client
from app.reviews.router import reviews_router
from app.telegram.service import telegram_service

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    try:
        redis_client.ping()
    except Exception:
        sys.exit(1)

    yield

    redis_client.close()
    await telegram_service.close()


app = FastAPI(
    lifespan=lifespan,
    title="Travelvv API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
)

app.include_router(login_router)
app.include_router(excursion_router)
app.include_router(reviews_router)
app.include_router(booking_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
