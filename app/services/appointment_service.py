from datetime import date, time

from fastapi import HTTPException, status

from app.core.statuses import AppointmentStatus
from app.models.appointment import Appointment
from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:
    def __init__(self, repository: AppointmentRepository):
        self.repository = repository

    def get_available_appointments(
            self,
            date_from: date | None = None,
            date_to: date | None = None
    ) -> list[Appointment]:
        effective_date_from = date_from if date_from is not None else date.today()
        self._validate_date_range(effective_date_from, date_to)

        return self.repository.get_available(
            date_from=effective_date_from,
            date_to=date_to
        )

    def get_appointment_by_id(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get_by_id(appointment_id)

        if appointment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Termin nije pronađen."
            )

        return appointment

    def get_all_appointments(self) -> list[Appointment]:
        return self.repository.get_all()

    def create_appointment(
            self,
            datum: date,
            vrijeme_od: time,
            vrijeme_do: time,
            status_value: str = AppointmentStatus.SLOBODAN.value
    ) -> Appointment:
        self._validate_time_range(vrijeme_od, vrijeme_do)
        self._validate_status(status_value)

        appointment = Appointment(
            Datum=datum,
            VrijemeOd=vrijeme_od,
            VrijemeDo=vrijeme_do,
            Status=status_value
        )

        return self.repository.create(appointment)

    def update_appointment(
            self,
            appointment_id: int,
            datum: date | None = None,
            vrijeme_od: time | None = None,
            vrijeme_do: time | None = None,
            status_value: str | None = None
    ) -> Appointment:
        appointment = self.get_appointment_by_id(appointment_id)

        new_vrijeme_od = vrijeme_od if vrijeme_od is not None else appointment.VrijemeOd
        new_vrijeme_do = vrijeme_do if vrijeme_do is not None else appointment.VrijemeDo
        self._validate_time_range(new_vrijeme_od, new_vrijeme_do)

        if status_value is not None:
            self._validate_status(status_value)
            appointment.Status = status_value

        if datum is not None:
            appointment.Datum = datum
        if vrijeme_od is not None:
            appointment.VrijemeOd = vrijeme_od
        if vrijeme_do is not None:
            appointment.VrijemeDo = vrijeme_do

        return self.repository.update(appointment)

    def delete_appointment(self, appointment_id: int) -> None:
        appointment = self.get_appointment_by_id(appointment_id)

        if appointment.Status == AppointmentStatus.ZAUZET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ovaj termin se može samo otkazati, a ne obrisati."
            )

        if (
            appointment.reservations
            or appointment.old_appointment_changes
            or appointment.new_appointment_changes
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ovaj termin se može samo otkazati, a ne obrisati."
            )

        self.repository.delete(appointment)

    def mark_as_occupied(self, appointment_id: int) -> Appointment:
        appointment = self.get_appointment_by_id(appointment_id)

        if appointment.Status != AppointmentStatus.SLOBODAN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Termin nije slobodan i ne može biti zauzet."
            )

        appointment.Status = AppointmentStatus.ZAUZET.value
        return self.repository.update(appointment)

    def mark_as_free(self, appointment_id: int) -> Appointment:
        appointment = self.get_appointment_by_id(appointment_id)

        if appointment.Status != AppointmentStatus.ZAUZET:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Termin nije u statusu 'zauzet' i ne može biti oslobođen."
            )

        appointment.Status = AppointmentStatus.SLOBODAN.value
        return self.repository.update(appointment)

    @staticmethod
    def _validate_status(status_value: str) -> None:
        try:
            AppointmentStatus(status_value)
        except ValueError:
            allowed = ", ".join(member.value for member in AppointmentStatus)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Neispravan status termina. Dozvoljeni: {allowed}."
            )

    @staticmethod
    def _validate_time_range(vrijeme_od: time, vrijeme_do: time) -> None:
        if vrijeme_do <= vrijeme_od:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vrijeme završetka mora biti veće od vremena početka."
            )

    @staticmethod
    def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_to < date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datum 'do' ne smije biti prije datuma 'od'."
            )
