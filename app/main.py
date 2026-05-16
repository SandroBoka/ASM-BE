from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health_routes import router as health_router
from app.api.routes.db_routes import router as db_router
from app.api.routes.service_routes import router as service_router
from app.api.routes.person_routes import router as person_router
from app.api.routes.vehicle_routes import router as vehicle_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.appointment_routes import router as appointment_router
from app.api.routes.reservation_routes import router as reservation_router
from app.api.routes.notification_routes import router as notification_router

app = FastAPI(
    title="ASM Backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router)
app.include_router(db_router)
app.include_router(service_router)
app.include_router(person_router)
app.include_router(vehicle_router)
app.include_router(auth_router)
app.include_router(appointment_router)
app.include_router(reservation_router)
app.include_router(notification_router)