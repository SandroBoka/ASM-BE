from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    ensure_admin_or_self,
    get_current_user,
    require_employee,
)
from app.core.auth_types import UserType
from app.db.database import get_db
from app.repositories.appointment_change_repository import AppointmentChangeRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas import AuthUserResponse
from app.schemas.appointment_change_schema import (
    AppointmentChangeActionRequest,
    AppointmentChangeRequest,
    AppointmentChangeResponse,
)
from app.services.appointment_change_service import AppointmentChangeService
from app.services.appointment_service import AppointmentService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/appointment-changes",
    tags=["Appointment Changes"]
)


def get_appointment_change_service(
        db: Session = Depends(get_db)
) -> AppointmentChangeService:
    change_repository = AppointmentChangeRepository(db)
    appointment_repository = AppointmentRepository(db)
    reservation_repository = ReservationRepository(db)
    appointment_service = AppointmentService(appointment_repository)

    return AppointmentChangeService(
        repository=change_repository,
        appointment_service=appointment_service,
        reservation_repository=reservation_repository,
    )


def get_reservation_repository(db: Session = Depends(get_db)) -> ReservationRepository:
    return ReservationRepository(db)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    repository = NotificationRepository(db)
    email_service = EmailService()
    return NotificationService(repository=repository, email_service=email_service)


def ensure_employee_or_reservation_owner(
        current_user: AuthUserResponse,
        owner_id: int
) -> None:
    if current_user.TipKorisnika == UserType.EMPLOYEE:
        return
    if current_user.IdOsobe == owner_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Pristup je dozvoljen samo vlasniku rezervacije ili zaposleniku."
    )


@router.post(
    "",
    response_model=AppointmentChangeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_change_request(
        request: AppointmentChangeRequest,
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        reservation_repository: ReservationRepository = Depends(get_reservation_repository),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    reservation = reservation_repository.get_by_id(request.IdRezervacije)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervacija nije pronađena."
        )
    ensure_admin_or_self(current_user, reservation.IdOsobe_Korisnik)

    return service.create_change_request(
        id_rezervacije=request.IdRezervacije,
        id_novog_termina=request.IdNovogTermina,
    )


@router.get("/pending", response_model=list[AppointmentChangeResponse])
def get_pending_changes(
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        _: AuthUserResponse = Depends(require_employee),
):
    return service.get_pending_changes()


@router.get(
    "/reservation/{reservation_id}",
    response_model=list[AppointmentChangeResponse]
)
def get_changes_for_reservation(
        reservation_id: int,
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        reservation_repository: ReservationRepository = Depends(get_reservation_repository),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    reservation = reservation_repository.get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervacija nije pronađena."
        )
    ensure_employee_or_reservation_owner(current_user, reservation.IdOsobe_Korisnik)

    return service.get_changes_by_reservation_id(reservation_id)


@router.get("", response_model=list[AppointmentChangeResponse])
def get_all_changes(
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        _: AuthUserResponse = Depends(require_employee),
):
    return service.get_all_changes()


@router.get("/{change_id}", response_model=AppointmentChangeResponse)
def get_change(
        change_id: int,
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        reservation_repository: ReservationRepository = Depends(get_reservation_repository),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    change = service.get_change_by_id(change_id)

    reservation = reservation_repository.get_by_id(change.IdRezervacije)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Povezana rezervacija nije pronađena."
        )
    ensure_employee_or_reservation_owner(current_user, reservation.IdOsobe_Korisnik)

    return change


@router.post("/{change_id}/accept", response_model=AppointmentChangeResponse)
def accept_change(
        change_id: int,
        request: AppointmentChangeActionRequest,
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_employee),
):
    change = service.accept_change(
        change_id=change_id,
        id_osobe_zaposlenik=current_user.IdOsobe,
        komentar=request.komentar,
    )

    notification_service.notify_change_accepted(change)

    return change


@router.post("/{change_id}/reject", response_model=AppointmentChangeResponse)
def reject_change(
        change_id: int,
        request: AppointmentChangeActionRequest,
        service: AppointmentChangeService = Depends(get_appointment_change_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_employee),
):
    change = service.reject_change(
        change_id=change_id,
        id_osobe_zaposlenik=current_user.IdOsobe,
        komentar=request.komentar,
    )

    notification_service.notify_change_rejected(change)

    return change
