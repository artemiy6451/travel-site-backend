from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import login_router
from app.config import settings
from app.redis_config import lifespan

# from app.excursions.router import excursion_router
# from app.reviews import router as reviews_router


app = FastAPI(
    lifespan=lifespan,
    title="Travelvv API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
)

app.include_router(login_router)
# app.include_router(excursion_router)
# app.include_router(reviews_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")
