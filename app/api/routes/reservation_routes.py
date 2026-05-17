from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    ensure_admin_or_self,
    get_current_user,
    require_employee,
)
from app.core.auth_types import UserType
from app.db.database import get_db
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas import AuthUserResponse
from app.schemas.reservation_schema import (
    ReservationActionRequest,
    ReservationCreate,
    ReservationResponse,
)
from app.services.appointment_service import AppointmentService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.reservation_service import ReservationService
from app.services.service_catalog_service import ServiceCatalogService
from app.services.vehicle_service import VehicleService

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)


def get_reservation_service(db: Session = Depends(get_db)) -> ReservationService:
    reservation_repository = ReservationRepository(db)
    appointment_repository = AppointmentRepository(db)
    vehicle_repository = VehicleRepository(db)
    service_repository = ServiceRepository(db)

    appointment_service = AppointmentService(appointment_repository)
    vehicle_service = VehicleService(vehicle_repository)
    service_catalog_service = ServiceCatalogService(service_repository)

    return ReservationService(
        repository=reservation_repository,
        appointment_service=appointment_service,
        vehicle_service=vehicle_service,
        service_catalog_service=service_catalog_service,
    )


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


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
        request: ReservationCreate,
        service: ReservationService = Depends(get_reservation_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    ensure_admin_or_self(current_user, request.IdOsobe_Korisnik)

    reservation = service.create_reservation(
        id_osobe_korisnik=request.IdOsobe_Korisnik,
        id_termina=request.IdTermina,
        id_vozila=request.IdVozila,
        kilometraza_vozila=request.KilometrazaVozila,
        opis_problema=request.OpisProblema,
        services=request.services,
    )

    notification_service.notify_reservation_created(reservation)

    return reservation


@router.get("/pending", response_model=list[ReservationResponse])
def get_pending_reservations(
        service: ReservationService = Depends(get_reservation_service),
        _: AuthUserResponse = Depends(require_employee),
):
    return service.get_pending_reservations()


@router.get("/customer/{customer_id}", response_model=list[ReservationResponse])
def get_reservations_for_customer(
        customer_id: int,
        service: ReservationService = Depends(get_reservation_service),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    ensure_employee_or_reservation_owner(current_user, customer_id)

    return service.get_reservations_by_customer_id(customer_id)


@router.get("", response_model=list[ReservationResponse])
def get_all_reservations(
        service: ReservationService = Depends(get_reservation_service),
        _: AuthUserResponse = Depends(require_employee),
):
    return service.get_all_reservations()


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
        reservation_id: int,
        service: ReservationService = Depends(get_reservation_service),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    reservation = service.get_reservation_by_id(reservation_id)
    ensure_employee_or_reservation_owner(current_user, reservation.IdOsobe_Korisnik)

    return reservation


@router.post("/{reservation_id}/approve", response_model=ReservationResponse)
def approve_reservation(
        reservation_id: int,
        request: ReservationActionRequest,
        service: ReservationService = Depends(get_reservation_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_employee),
):
    reservation = service.approve_reservation(
        reservation_id=reservation_id,
        id_osobe_zaposlenik=current_user.IdOsobe,
        komentar=request.komentar,
    )

    notification_service.notify_reservation_approved(reservation)

    return reservation


@router.post("/{reservation_id}/reject", response_model=ReservationResponse)
def reject_reservation(
        reservation_id: int,
        request: ReservationActionRequest,
        service: ReservationService = Depends(get_reservation_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(require_employee),
):
    reservation = service.reject_reservation(
        reservation_id=reservation_id,
        id_osobe_zaposlenik=current_user.IdOsobe,
        komentar=request.komentar,
    )

    notification_service.notify_reservation_rejected(reservation)

    return reservation


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(
        reservation_id: int,
        request: ReservationActionRequest,
        service: ReservationService = Depends(get_reservation_service),
        notification_service: NotificationService = Depends(get_notification_service),
        current_user: AuthUserResponse = Depends(get_current_user),
):
    reservation = service.get_reservation_by_id(reservation_id)
    ensure_admin_or_self(current_user, reservation.IdOsobe_Korisnik)

    canceled = service.cancel_reservation(
        reservation_id=reservation_id,
        komentar=request.komentar,
    )

    notification_service.notify_reservation_canceled(canceled)

    return canceled


@router.post("/{reservation_id}/complete", response_model=ReservationResponse)
def complete_reservation(
        reservation_id: int,
        service: ReservationService = Depends(get_reservation_service),
        _: AuthUserResponse = Depends(require_employee),
):
    return service.complete_reservation(reservation_id)
