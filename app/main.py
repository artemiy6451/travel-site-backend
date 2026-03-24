import locale
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.auth.router import auth_router
from app.booking.router import booking_router
from app.config import settings
from app.details.router import details_router
from app.excursions.router import excursion_router
from app.images.router import image_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.notifications.router import notifications_router
from app.reviews.router import reviews_router
from app.user.router import user_router
from app.utils.cron import (
    cron_manager,
    deactivate_past_bookings,
    deactivate_past_excurions_cron,
)
from app.utils.logging import setup_new_logger
from app.utils.redis_config import redis_client

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
setup_new_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting application...", mode=settings.mode)
    try:
        redis_client.ping()
        logger.success("Redis connected successfully")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        sys.exit(1)

    deactivate_past_excurions_cron()
    deactivate_past_bookings()

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

LOCAL_ONLY_PATHS = {"/health", "/metrics"}
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


@app.middleware("http")
async def restrict_internal_routes(request: Request, call_next: Callable) -> Any:
    """Restrict /health and /metrics to localhost in production."""
    if (
        settings.is_production
        and request.url.path in LOCAL_ONLY_PATHS
        and request.client
        and request.client.host not in LOCAL_HOSTS
    ):
        logger.warning(
            "Blocked external access to internal endpoint",
            path=request.url.path,
            host=request.client.host,
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Endpoint available from localhost only"},
        )
    return await call_next(request)


logger.info("Setting up routes...")
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(excursion_router)
app.include_router(details_router)
app.include_router(image_router)
app.include_router(booking_router)
app.include_router(reviews_router)
app.include_router(notifications_router)
logger.success("Routes setup complete")


app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")


@app.get("/health")
async def health_check() -> dict:
    logger.debug("Health check requested")
    return {"status": "healthy"}


logger.success(
    f"Application '{app.title}' in '{settings.mode}' mode v{app.version} is ready!"
)
