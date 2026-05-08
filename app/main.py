from fastapi import FastAPI
from app.api.routes.health_routes import router as health_router

app = FastAPI(
    title="ASM Backend",
    version="0.1.0"
)


app.include_router(health_router)
