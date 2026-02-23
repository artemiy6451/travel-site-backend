import locale
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.auth.router import login_router
from app.booking.router import booking_router
from app.config import settings
from app.cron import cron_manager, deactivate_past_excurions_cron
from app.excursions.router import excursion_router
from app.logging import setup_new_logger
from app.middleware.logging_middleware import LoggingMiddleware
from app.redis_config import redis_client
from app.reviews.router import reviews_router

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
setup_new_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    logger.info("Starting application...", mode=settings.mode)
    try:
        redis_client.ping()
        logger.success("Redis connected successfully")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        sys.exit(1)

    deactivate_past_excurions_cron()

    yield

    redis_client.close()
    cron_manager.stop_all()
    logger.info("Shutting down application...")


app = FastAPI(
    lifespan=lifespan,
    title="Travelvv API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
)

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Setting up routes...")
app.include_router(login_router)
app.include_router(excursion_router)
app.include_router(reviews_router)
app.include_router(booking_router)
logger.success("Routes setup complete")


app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")


@app.get("/health")
async def health_check() -> dict:
    logger.debug("Health check requested")
    return {"status": "healthy"}


logger.success(
    f"Application '{app.title}' in '{settings.mode}' mode v{app.version} is ready!"
)
