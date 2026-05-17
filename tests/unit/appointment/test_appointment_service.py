from datetime import date, time, timedelta

import pytest
from fastapi import HTTPException

from app.core.statuses import AppointmentStatus
from app.models.appointment_change import AppointmentChange
from app.models.reservation import Reservation
from app.services.appointment_service import AppointmentService


class FakeAppointmentRepository:
    def __init__(self):
        self.appointments = []
        self.next_id = 1
        self.last_get_available_args = None

    def get_by_id(self, appointment_id):
        for appointment in self.appointments:
            if appointment.IdTermina == appointment_id:
                return appointment
        return None

    def get_all(self):
        return list(self.appointments)

    def get_available(self, date_from=None, date_to=None):
        self.last_get_available_args = (date_from, date_to)
        result = []
        for appointment in self.appointments:
            if appointment.Status != AppointmentStatus.SLOBODAN.value:
                continue
            if date_from is not None and appointment.Datum < date_from:
                continue
            if date_to is not None and appointment.Datum > date_to:
                continue
            result.append(appointment)
        return result

    def create(self, appointment):
        appointment.IdTermina = self.next_id
        self.next_id += 1
        appointment.reservations = []
        appointment.old_appointment_changes = []
        appointment.new_appointment_changes = []
        self.appointments.append(appointment)
        return appointment

    def update(self, appointment):
        return appointment

    def delete(self, appointment):
        self.appointments.remove(appointment)


def _make_service():
    repository = FakeAppointmentRepository()
    service = AppointmentService(repository)
    return service, repository


def test_get_available_appointments_uses_today_when_no_date_from():
    service, repository = _make_service()

    service.get_available_appointments()

    assert repository.last_get_available_args == (date.today(), None)


def test_get_available_appointments_with_explicit_range():
    service, repository = _make_service()

    date_from = date(2026, 1, 1)
    date_to = date(2026, 1, 31)

    service.get_available_appointments(date_from=date_from, date_to=date_to)

    assert repository.last_get_available_args == (date_from, date_to)


def test_get_available_appointments_fails_when_date_to_before_date_from():
    service, _ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.get_available_appointments(
            date_from=date(2026, 5, 10),
            date_to=date(2026, 5, 1),
        )

    assert error.value.status_code == 400
    assert "Datum 'do' ne smije biti prije datuma 'od'." in error.value.detail


def test_get_appointment_by_id_not_found():
    service, _ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.get_appointment_by_id(999)

    assert error.value.status_code == 404
    assert error.value.detail == "Termin nije pronađen."


def test_get_appointment_by_id_success():
    service, _ = _make_service()

    created = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    found = service.get_appointment_by_id(created.IdTermina)

    assert found.IdTermina == created.IdTermina


def test_create_appointment_success_with_default_status():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    assert appointment.IdTermina == 1
    assert appointment.Datum == date(2026, 5, 1)
    assert appointment.VrijemeOd == time(9, 0)
    assert appointment.VrijemeDo == time(10, 0)
    assert appointment.Status == AppointmentStatus.SLOBODAN.value


def test_create_appointment_fails_when_vrijeme_do_not_greater_than_vrijeme_od():
    service, _ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.create_appointment(
            datum=date(2026, 5, 1),
            vrijeme_od=time(10, 0),
            vrijeme_do=time(10, 0),
        )

    assert error.value.status_code == 400
    assert "Vrijeme završetka mora biti veće od vremena početka." in error.value.detail


def test_create_appointment_fails_with_invalid_status():
    service, _ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.create_appointment(
            datum=date(2026, 5, 1),
            vrijeme_od=time(9, 0),
            vrijeme_do=time(10, 0),
            status_value="nepoznato",
        )

    assert error.value.status_code == 400
    assert "Neispravan status termina" in error.value.detail


def test_update_appointment_partial_update():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    updated = service.update_appointment(
        appointment_id=appointment.IdTermina,
        datum=date(2026, 5, 2),
        vrijeme_od=time(11, 0),
        vrijeme_do=time(12, 30),
        status_value=AppointmentStatus.ZAUZET.value,
    )

    assert updated.Datum == date(2026, 5, 2)
    assert updated.VrijemeOd == time(11, 0)
    assert updated.VrijemeDo == time(12, 30)
    assert updated.Status == AppointmentStatus.ZAUZET.value


def test_update_appointment_fails_when_resulting_time_invalid():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    with pytest.raises(HTTPException) as error:
        # only changing vrijeme_od to be >= existing vrijeme_do
        service.update_appointment(
            appointment_id=appointment.IdTermina,
            vrijeme_od=time(10, 30),
        )

    assert error.value.status_code == 400


def test_delete_appointment_not_found():
    service, _ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.delete_appointment(999)

    assert error.value.status_code == 404


def test_delete_appointment_fails_when_occupied():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
        status_value=AppointmentStatus.ZAUZET.value,
    )

    with pytest.raises(HTTPException) as error:
        service.delete_appointment(appointment.IdTermina)

    assert error.value.status_code == 400
    assert "otkazati" in error.value.detail


def test_delete_appointment_fails_when_has_reservations_or_changes():
    service, repository = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )
    appointment.reservations = [Reservation()]

    with pytest.raises(HTTPException) as error:
        service.delete_appointment(appointment.IdTermina)

    assert error.value.status_code == 400

    appointment.reservations = []
    appointment.old_appointment_changes = [AppointmentChange()]

    with pytest.raises(HTTPException) as error:
        service.delete_appointment(appointment.IdTermina)

    assert error.value.status_code == 400

    appointment.old_appointment_changes = []
    appointment.new_appointment_changes = [AppointmentChange()]

    with pytest.raises(HTTPException) as error:
        service.delete_appointment(appointment.IdTermina)

    assert error.value.status_code == 400


def test_delete_appointment_success_when_free_and_empty():
    service, repository = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    service.delete_appointment(appointment.IdTermina)

    assert repository.get_by_id(appointment.IdTermina) is None


def test_mark_as_occupied_success():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    updated = service.mark_as_occupied(appointment.IdTermina)

    assert updated.Status == AppointmentStatus.ZAUZET.value


def test_mark_as_occupied_conflict_when_not_free():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
        status_value=AppointmentStatus.ZAUZET.value,
    )

    with pytest.raises(HTTPException) as error:
        service.mark_as_occupied(appointment.IdTermina)

    assert error.value.status_code == 409


def test_mark_as_free_success():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
        status_value=AppointmentStatus.ZAUZET.value,
    )

    updated = service.mark_as_free(appointment.IdTermina)

    assert updated.Status == AppointmentStatus.SLOBODAN.value


def test_mark_as_free_conflict_when_not_occupied():
    service, _ = _make_service()

    appointment = service.create_appointment(
        datum=date(2026, 5, 1),
        vrijeme_od=time(9, 0),
        vrijeme_do=time(10, 0),
    )

    with pytest.raises(HTTPException) as error:
        service.mark_as_free(appointment.IdTermina)

    assert error.value.status_code == 409
