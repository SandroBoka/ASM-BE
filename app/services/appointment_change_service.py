from fastapi import HTTPException, status

from app.core.statuses import (
    AppointmentChangeStatus,
    AppointmentStatus,
    ReservationStatus,
)
from app.models.appointment_change import AppointmentChange
from app.repositories.appointment_change_repository import AppointmentChangeRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.appointment_service import AppointmentService


class AppointmentChangeService:
    ALLOWED_TRANSITIONS: dict[AppointmentChangeStatus, set[AppointmentChangeStatus]] = {
        AppointmentChangeStatus.NA_CEKANJU: {
            AppointmentChangeStatus.PRIHVACEN,
            AppointmentChangeStatus.ODBIJEN,
        },
    }

    def __init__(
            self,
            repository: AppointmentChangeRepository,
            appointment_service: AppointmentService,
            reservation_repository: ReservationRepository,
    ):
        self.repository = repository
        self.appointment_service = appointment_service
        self.reservation_repository = reservation_repository

    def get_all_changes(self) -> list[AppointmentChange]:
        return self.repository.get_all()

    def get_pending_changes(self) -> list[AppointmentChange]:
        return self.repository.get_by_status(AppointmentChangeStatus.NA_CEKANJU.value)

    def get_change_by_id(self, change_id: int) -> AppointmentChange:
        change = self.repository.get_by_id(change_id)

        if change is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zahtjev za promjenu termina nije pronađen."
            )

        return change

    def get_changes_by_reservation_id(self, reservation_id: int) -> list[AppointmentChange]:
        return self.repository.get_by_reservation_id(reservation_id)

    def create_change_request(
            self,
            id_rezervacije: int,
            id_novog_termina: int,
    ) -> AppointmentChange:
        reservation = self.reservation_repository.get_by_id(id_rezervacije)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezervacija nije pronađena."
            )

        if reservation.Status != ReservationStatus.ODOBRENA:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Promjena termina je moguća samo za odobrene rezervacije."
            )

        if reservation.IdTermina == id_novog_termina:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Novi termin mora biti različit od trenutnog termina rezervacije."
            )

        new_appointment = self.appointment_service.get_appointment_by_id(id_novog_termina)
        if new_appointment.Status != AppointmentStatus.SLOBODAN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Predloženi novi termin nije slobodan."
            )

        change = AppointmentChange(
            Status=AppointmentChangeStatus.NA_CEKANJU.value,
            IdRezervacije=id_rezervacije,
            IdStarogTermina=reservation.IdTermina,
            IdNovogTermina=id_novog_termina,
        )

        return self.repository.create(change)

    def accept_change(
            self,
            change_id: int,
            id_osobe_zaposlenik: int,
            komentar: str | None = None,
    ) -> AppointmentChange:
        change = self.get_change_by_id(change_id)
        self._validate_transition(change.Status, AppointmentChangeStatus.PRIHVACEN)

        reservation = self.reservation_repository.get_by_id(change.IdRezervacije)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Povezana rezervacija nije pronađena."
            )
        if reservation.Status != ReservationStatus.ODOBRENA:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Povezana rezervacija više nije u statusu 'odobrena'. "
                    "Zahtjev za promjenu termina nije moguće prihvatiti."
                )
            )

        new_appointment = self.appointment_service.get_appointment_by_id(change.IdNovogTermina)
        if new_appointment.Status != AppointmentStatus.SLOBODAN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Predloženi novi termin više nije slobodan. "
                    "Zahtjev je potrebno odbiti."
                )
            )

        self.appointment_service.mark_as_free(change.IdStarogTermina)
        self.appointment_service.mark_as_occupied(change.IdNovogTermina)

        reservation.IdTermina = change.IdNovogTermina
        self.reservation_repository.update(reservation)

        change.Status = AppointmentChangeStatus.PRIHVACEN.value
        change.IdOsobe_Zaposlenik = id_osobe_zaposlenik
        if komentar is not None:
            change.KomentarZaposlenika = komentar.strip() or None

        return self.repository.update(change)

    def reject_change(
            self,
            change_id: int,
            id_osobe_zaposlenik: int,
            komentar: str | None = None,
    ) -> AppointmentChange:
        change = self.get_change_by_id(change_id)
        self._validate_transition(change.Status, AppointmentChangeStatus.ODBIJEN)

        change.Status = AppointmentChangeStatus.ODBIJEN.value
        change.IdOsobe_Zaposlenik = id_osobe_zaposlenik
        if komentar is not None:
            change.KomentarZaposlenika = komentar.strip() or None

        return self.repository.update(change)

    def _validate_transition(
            self,
            current_status: str,
            target_status: AppointmentChangeStatus,
    ) -> None:
        try:
            current = AppointmentChangeStatus(current_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nepoznat trenutni status zahtjeva: {current_status!r}."
            )

        allowed = self.ALLOWED_TRANSITIONS.get(current, set())
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Tranzicija statusa zahtjeva za promjenu termina iz "
                    f"'{current.value}' u '{target_status.value}' nije dozvoljena."
                )
            )
