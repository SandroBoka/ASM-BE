from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService
from app.api.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"],
    dependencies=[Depends(get_current_user)]
)


def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    repository = VehicleRepository(db)
    return VehicleService(repository)


@router.get("/customers/{customer_id}", response_model=list[VehicleResponse])
def get_customer_vehicles(customer_id: int, service: VehicleService = Depends(get_vehicle_service)):
    return service.get_vehicles_by_customer_id(customer_id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, service: VehicleService = Depends(get_vehicle_service)):
    return service.get_vehicle_by_id(vehicle_id)


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
        request: VehicleCreate,
        service: VehicleService = Depends(get_vehicle_service)
):
    return service.create_vehicle(
        marka=request.Marka,
        model=request.Model,
        godina=request.Godina,
        vrsta_motora=request.VrstaMotora,
        reg_oznaka=request.RegOznaka,
        id_osobe=request.IdOsobe
    )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
        vehicle_id: int,
        request: VehicleUpdate,
        service: VehicleService = Depends(get_vehicle_service)
):
    return service.update_vehicle(
        vehicle_id=vehicle_id,
        marka=request.Marka,
        model=request.Model,
        godina=request.Godina,
        vrsta_motora=request.VrstaMotora,
        reg_oznaka=request.RegOznaka
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, service: VehicleService = Depends(get_vehicle_service)):
    service.delete_vehicle(vehicle_id)
