from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    get_current_user,
    require_employee,
    require_role,
)
from app.core.auth_types import EmployeeRole
from app.db.database import get_db
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas import AuthUserResponse
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def get_appointment_service(db: Session = Depends(get_db)) -> AppointmentService:
    repository = AppointmentRepository(db)
    return AppointmentService(repository)


@router.get("/free", response_model=list[AppointmentResponse])
def get_free_appointments(
        date_from: date | None = Query(default=None),
        date_to: date | None = Query(default=None),
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(get_current_user)
):
    return service.get_available_appointments(date_from=date_from, date_to=date_to)


@router.get("", response_model=list[AppointmentResponse])
def get_all_appointments(
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(require_employee)
):
    return service.get_all_appointments()


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
        appointment_id: int,
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(get_current_user)
):
    return service.get_appointment_by_id(appointment_id)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
        request: AppointmentCreate,
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(require_role(EmployeeRole.ADMIN, EmployeeRole.VODITELJ))
):
    return service.create_appointment(
        datum=request.Datum,
        vrijeme_od=request.VrijemeOd,
        vrijeme_do=request.VrijemeDo,
        status_value=request.Status
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
        appointment_id: int,
        request: AppointmentUpdate,
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(require_role(EmployeeRole.ADMIN, EmployeeRole.VODITELJ))
):
    return service.update_appointment(
        appointment_id=appointment_id,
        datum=request.Datum,
        vrijeme_od=request.VrijemeOd,
        vrijeme_do=request.VrijemeDo,
        status_value=request.Status
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
        appointment_id: int,
        service: AppointmentService = Depends(get_appointment_service),
        _: AuthUserResponse = Depends(require_role(EmployeeRole.ADMIN, EmployeeRole.VODITELJ))
):
    service.delete_appointment(appointment_id)
