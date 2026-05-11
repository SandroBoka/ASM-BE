from fastapi import FastAPI
from app.api.routes.health_routes import router as health_router
from app.api.routes.db_routes import router as db_router
from app.api.routes.service_routes import router as service_router
from app.api.routes.person_routes import router as person_router
from app.api.routes.vehicle_routes import router as vehicle_router

app = FastAPI(
    title="ASM Backend",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(db_router)
app.include_router(service_router)
app.include_router(person_router)
app.include_router(vehicle_router)
