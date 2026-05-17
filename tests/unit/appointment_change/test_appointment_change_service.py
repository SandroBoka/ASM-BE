from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.statuses import (
    AppointmentChangeStatus,
    AppointmentStatus,
    ReservationStatus,
)
from app.services.appointment_change_service import AppointmentChangeService


class FakeAppointmentChangeRepository:
    def __init__(self):
        self.changes = []
        self.next_id = 1

    def get_all(self):
        return list(self.changes)

    def get_by_id(self, change_id):
        for change in self.changes:
            if change.IdZahtjevaPromjene == change_id:
                return change
        return None

    def get_by_reservation_id(self, reservation_id):
        return [c for c in self.changes if c.IdRezervacije == reservation_id]

    def get_by_status(self, status_value):
        return [c for c in self.changes if c.Status == status_value]

    def create(self, change):
        change.IdZahtjevaPromjene = self.next_id
        self.next_id += 1
        if not hasattr(change, "IdOsobe_Zaposlenik"):
            change.IdOsobe_Zaposlenik = None
        if not hasattr(change, "KomentarZaposlenika"):
            change.KomentarZaposlenika = None
        self.changes.append(change)
        return change

    def update(self, change):
        return change


class FakeReservationRepository:
    def __init__(self):
        self.reservations = []
        self.updated = []

    def add(self, reservation):
        self.reservations.append(reservation)
        return reservation

    def get_by_id(self, reservation_id):
        for reservation in self.reservations:
            if reservation.IdRezervacije == reservation_id:
                return reservation
        return None

    def update(self, reservation):
        self.updated.append(reservation)
        return reservation


class FakeAppointmentService:
    def __init__(self):
        self.appointments = {}
        self.mark_as_occupied_calls = []
        self.mark_as_free_calls = []

    def add(self, appointment_id, status_value=AppointmentStatus.SLOBODAN.value):
        appointment = SimpleNamespace(
            IdTermina=appointment_id,
            Status=status_value,
        )
        self.appointments[appointment_id] = appointment
        return appointment

    def get_appointment_by_id(self, appointment_id):
        if appointment_id not in self.appointments:
            raise HTTPException(status_code=404, detail="Termin nije pronađen.")
        return self.appointments[appointment_id]

    def mark_as_occupied(self, appointment_id):
        self.mark_as_occupied_calls.append(appointment_id)
        appointment = self.get_appointment_by_id(appointment_id)
        appointment.Status = AppointmentStatus.ZAUZET.value
        return appointment

    def mark_as_free(self, appointment_id):
        self.mark_as_free_calls.append(appointment_id)
        appointment = self.get_appointment_by_id(appointment_id)
        appointment.Status = AppointmentStatus.SLOBODAN.value
        return appointment


def _make_service():
    change_repository = FakeAppointmentChangeRepository()
    appointment_service = FakeAppointmentService()
    reservation_repository = FakeReservationRepository()
    service = AppointmentChangeService(
        repository=change_repository,
        appointment_service=appointment_service,
        reservation_repository=reservation_repository,
    )
    return service, change_repository, appointment_service, reservation_repository


def _make_reservation(reservation_id=1, status_value=ReservationStatus.ODOBRENA.value, id_termina=1):
    return SimpleNamespace(
        IdRezervacije=reservation_id,
        Status=status_value,
        IdTermina=id_termina,
    )


def test_create_change_request_success():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    reservation_repository.add(_make_reservation())
    appointment_service.add(1, status_value=AppointmentStatus.ZAUZET.value)
    appointment_service.add(2, status_value=AppointmentStatus.SLOBODAN.value)

    change = service.create_change_request(id_rezervacije=1, id_novog_termina=2)

    assert change.IdZahtjevaPromjene == 1
    assert change.Status == AppointmentChangeStatus.NA_CEKANJU.value
    assert change.IdRezervacije == 1
    assert change.IdStarogTermina == 1
    assert change.IdNovogTermina == 2


def test_create_change_request_fails_when_reservation_not_found():
    service, *_ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.create_change_request(id_rezervacije=999, id_novog_termina=2)

    assert error.value.status_code == 404
    assert error.value.detail == "Rezervacija nije pronađena."


def test_create_change_request_fails_when_reservation_not_approved():
    service, _, appointment_service, reservation_repository = _make_service()
    reservation_repository.add(_make_reservation(status_value=ReservationStatus.NA_CEKANJU.value))
    appointment_service.add(2)

    with pytest.raises(HTTPException) as error:
        service.create_change_request(id_rezervacije=1, id_novog_termina=2)

    assert error.value.status_code == 409
    assert "odobrene" in error.value.detail


def test_create_change_request_fails_when_new_is_same_as_old():
    service, _, appointment_service, reservation_repository = _make_service()
    reservation_repository.add(_make_reservation(id_termina=2))
    appointment_service.add(2)

    with pytest.raises(HTTPException) as error:
        service.create_change_request(id_rezervacije=1, id_novog_termina=2)

    assert error.value.status_code == 400
    assert "različit" in error.value.detail


def test_create_change_request_fails_when_new_appointment_not_free():
    service, _, appointment_service, reservation_repository = _make_service()
    reservation_repository.add(_make_reservation())
    appointment_service.add(1, status_value=AppointmentStatus.ZAUZET.value)
    appointment_service.add(2, status_value=AppointmentStatus.ZAUZET.value)

    with pytest.raises(HTTPException) as error:
        service.create_change_request(id_rezervacije=1, id_novog_termina=2)

    assert error.value.status_code == 409
    assert "slobodan" in error.value.detail


def _seed_pending_change(change_repo, appointment_service, reservation_repository,
                         old_id=1, new_id=2,
                         reservation_status=ReservationStatus.ODOBRENA.value,
                         old_status=AppointmentStatus.ZAUZET.value,
                         new_status=AppointmentStatus.SLOBODAN.value):
    reservation = _make_reservation(status_value=reservation_status, id_termina=old_id)
    reservation_repository.add(reservation)
    appointment_service.add(old_id, status_value=old_status)
    appointment_service.add(new_id, status_value=new_status)
    change = SimpleNamespace(
        IdZahtjevaPromjene=1,
        Status=AppointmentChangeStatus.NA_CEKANJU.value,
        IdRezervacije=1,
        IdStarogTermina=old_id,
        IdNovogTermina=new_id,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    change_repo.changes.append(change)
    change_repo.next_id = 2
    return change, reservation


def test_accept_change_success():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    change, reservation = _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
    )

    result = service.accept_change(
        change_id=1,
        id_osobe_zaposlenik=200,
        komentar="   ok   ",
    )

    assert result.Status == AppointmentChangeStatus.PRIHVACEN.value
    assert result.IdOsobe_Zaposlenik == 200
    assert result.KomentarZaposlenika == "ok"
    assert 1 in appointment_service.mark_as_free_calls
    assert 2 in appointment_service.mark_as_occupied_calls
    assert reservation.IdTermina == 2
    assert reservation in reservation_repository.updated


def test_accept_change_fails_when_reservation_not_found():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    # Add change but no reservation
    appointment_service.add(1, status_value=AppointmentStatus.ZAUZET.value)
    appointment_service.add(2)
    change = SimpleNamespace(
        IdZahtjevaPromjene=1,
        Status=AppointmentChangeStatus.NA_CEKANJU.value,
        IdRezervacije=42,  # no such reservation
        IdStarogTermina=1,
        IdNovogTermina=2,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    change_repo.changes.append(change)

    with pytest.raises(HTTPException) as error:
        service.accept_change(change_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 404
    assert "Povezana rezervacija" in error.value.detail


def test_accept_change_conflict_when_reservation_no_longer_approved():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
        reservation_status=ReservationStatus.OTKAZANA.value,
    )

    with pytest.raises(HTTPException) as error:
        service.accept_change(change_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "odobrena" in error.value.detail


def test_accept_change_conflict_when_new_appointment_no_longer_free():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
        new_status=AppointmentStatus.ZAUZET.value,
    )

    with pytest.raises(HTTPException) as error:
        service.accept_change(change_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "slobodan" in error.value.detail


def test_accept_change_conflict_on_invalid_transition():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    change, _ = _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
    )
    # Move change to PRIHVACEN; re-accepting it should fail validation
    change.Status = AppointmentChangeStatus.PRIHVACEN.value

    with pytest.raises(HTTPException) as error:
        service.accept_change(change_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "Tranzicija" in error.value.detail


def test_reject_change_success():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    change, reservation = _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
    )

    result = service.reject_change(
        change_id=1,
        id_osobe_zaposlenik=200,
        komentar="ne",
    )

    assert result.Status == AppointmentChangeStatus.ODBIJEN.value
    assert result.IdOsobe_Zaposlenik == 200
    assert result.KomentarZaposlenika == "ne"
    # Appointments and reservation untouched
    assert appointment_service.mark_as_free_calls == []
    assert appointment_service.mark_as_occupied_calls == []
    assert reservation.IdTermina == 1
    assert reservation_repository.updated == []


def test_reject_change_conflict_on_invalid_transition():
    service, change_repo, appointment_service, reservation_repository = _make_service()
    change, _ = _seed_pending_change(
        change_repo, appointment_service, reservation_repository,
    )
    change.Status = AppointmentChangeStatus.ODBIJEN.value

    with pytest.raises(HTTPException) as error:
        service.reject_change(change_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "Tranzicija" in error.value.detail
