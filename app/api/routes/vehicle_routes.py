from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, is_admin, ensure_admin_or_self
from app.core.auth_types import UserType
from app.db.database import get_db
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas import AuthUserResponse
from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    repository = VehicleRepository(db)
    return VehicleService(repository)


def ensure_employee_or_vehicle_owner(current_user: AuthUserResponse, owner_id: int) -> None:
    if current_user.TipKorisnika == UserType.EMPLOYEE or current_user.IdOsobe == owner_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Možete pristupiti samo vlastitim vozilima"
    )


def ensure_admin_or_vehicle_owner(current_user: AuthUserResponse, owner_id: int) -> None:
    if is_admin(current_user) or current_user.IdOsobe == owner_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Možete mijenjati samo vlastita vozila"
    )


@router.get("/customers/{customer_id}", response_model=list[VehicleResponse])
def get_customer_vehicles(
        customer_id: int,
        service: VehicleService = Depends(get_vehicle_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    ensure_employee_or_vehicle_owner(current_user, customer_id)

    return service.get_vehicles_by_customer_id(customer_id)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
        vehicle_id: int,
        service: VehicleService = Depends(get_vehicle_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    vehicle = service.get_vehicle_by_id(vehicle_id)
    ensure_employee_or_vehicle_owner(current_user, vehicle.IdOsobe)

    return vehicle


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
        request: VehicleCreate,
        service: VehicleService = Depends(get_vehicle_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    ensure_admin_or_self(current_user, request.IdOsobe)

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
        service: VehicleService = Depends(get_vehicle_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    vehicle = service.get_vehicle_by_id(vehicle_id)
    ensure_admin_or_vehicle_owner(current_user, vehicle.IdOsobe)

    return service.update_vehicle(
        vehicle_id=vehicle_id,
        marka=request.Marka,
        model=request.Model,
        godina=request.Godina,
        vrsta_motora=request.VrstaMotora,
        reg_oznaka=request.RegOznaka
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
        vehicle_id: int,
        service: VehicleService = Depends(get_vehicle_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    vehicle = service.get_vehicle_by_id(vehicle_id)
    ensure_admin_or_vehicle_owner(current_user, vehicle.IdOsobe)

    service.delete_vehicle(vehicle_id)
