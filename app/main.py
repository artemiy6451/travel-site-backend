from auth.router import login_router
from excursions.router import excursion_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
