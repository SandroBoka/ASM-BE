from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.statuses import AppointmentStatus, ReservationStatus
from app.schemas.reservation_schema import ReservationServiceItemCreate
from app.services.reservation_service import ReservationService


class FakeDb:
    def refresh(self, obj):
        return None


class FakeReservationRepository:
    def __init__(self):
        self.reservations = []
        self.service_links = []
        self.next_id = 1
        self.db = FakeDb()

    def get_all(self):
        return list(self.reservations)

    def get_by_id(self, reservation_id):
        for reservation in self.reservations:
            if reservation.IdRezervacije == reservation_id:
                return reservation
        return None

    def get_by_customer_id(self, person_id):
        return [
            r for r in self.reservations if r.IdOsobe_Korisnik == person_id
        ]

    def get_by_status(self, status_value):
        return [r for r in self.reservations if r.Status == status_value]

    def get_approved_by_appointment_id(self, appointment_id):
        for reservation in self.reservations:
            if (
                reservation.IdTermina == appointment_id
                and reservation.Status == ReservationStatus.ODOBRENA.value
            ):
                return reservation
        return None

    def create(self, reservation):
        reservation.IdRezervacije = self.next_id
        self.next_id += 1
        # Ensure attribute exists for service updates
        if not hasattr(reservation, "KomentarZaposlenika"):
            reservation.KomentarZaposlenika = None
        if not hasattr(reservation, "IdOsobe_Zaposlenik"):
            reservation.IdOsobe_Zaposlenik = None
        self.reservations.append(reservation)
        return reservation

    def add_service(self, link):
        self.service_links.append(link)
        return link

    def delete_services(self, reservation_id):
        self.service_links = [
            link for link in self.service_links if link.IdRezervacije != reservation_id
        ]

    def get_service_link(self, reservation_id, id_usluge):
        for link in self.service_links:
            if link.IdRezervacije == reservation_id and link.IdUsluge == id_usluge:
                return link
        return None

    def update_service_link(self, link):
        return link

    def delete_service_link(self, link):
        self.service_links.remove(link)

    def update(self, reservation):
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


class FakeVehicleService:
    def __init__(self):
        self.vehicles = {}

    def add(self, vehicle_id, id_osobe):
        vehicle = SimpleNamespace(IdVozila=vehicle_id, IdOsobe=id_osobe)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def get_vehicle_by_id(self, vehicle_id):
        if vehicle_id not in self.vehicles:
            raise HTTPException(status_code=404, detail="Vozilo nije pronađeno.")
        return self.vehicles[vehicle_id]


class FakeServiceCatalogService:
    def __init__(self):
        self.services = {}

    def add(self, service_id):
        catalog = SimpleNamespace(IdUsluge=service_id)
        self.services[service_id] = catalog
        return catalog

    def get_service_by_id(self, service_id):
        if service_id not in self.services:
            raise HTTPException(status_code=404, detail="Usluga nije pronađena.")
        return self.services[service_id]


def _make_service():
    repository = FakeReservationRepository()
    appointment_service = FakeAppointmentService()
    vehicle_service = FakeVehicleService()
    service_catalog_service = FakeServiceCatalogService()
    service = ReservationService(
        repository=repository,
        appointment_service=appointment_service,
        vehicle_service=vehicle_service,
        service_catalog_service=service_catalog_service,
    )
    return service, repository, appointment_service, vehicle_service, service_catalog_service


def _setup_world(appointment_service, vehicle_service, service_catalog_service):
    appointment_service.add(1)
    vehicle_service.add(10, id_osobe=100)
    service_catalog_service.add(1000)


def _services_payload():
    return [ReservationServiceItemCreate(IdUsluge=1000, Kolicina=2)]


def test_get_all_reservations_delegates_to_repository():
    service, repository, *_ = _make_service()
    repository.reservations.append(SimpleNamespace(IdRezervacije=1))

    result = service.get_all_reservations()

    assert len(result) == 1


def test_get_pending_reservations_delegates_to_repository():
    service, repository, *_ = _make_service()
    repository.reservations.append(SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
    ))
    repository.reservations.append(SimpleNamespace(
        IdRezervacije=2,
        Status=ReservationStatus.ODOBRENA.value,
    ))

    pending = service.get_pending_reservations()

    assert len(pending) == 1
    assert pending[0].IdRezervacije == 1


def test_get_reservations_by_customer_id():
    service, repository, *_ = _make_service()
    repository.reservations.append(SimpleNamespace(
        IdRezervacije=1, IdOsobe_Korisnik=100,
    ))
    repository.reservations.append(SimpleNamespace(
        IdRezervacije=2, IdOsobe_Korisnik=200,
    ))

    result = service.get_reservations_by_customer_id(100)

    assert len(result) == 1


def test_get_reservation_by_id_not_found():
    service, *_ = _make_service()

    with pytest.raises(HTTPException) as error:
        service.get_reservation_by_id(999)

    assert error.value.status_code == 404
    assert error.value.detail == "Rezervacija nije pronađena."


def test_get_reservation_by_id_success():
    service, repository, *_ = _make_service()
    repository.reservations.append(SimpleNamespace(IdRezervacije=5))

    result = service.get_reservation_by_id(5)

    assert result.IdRezervacije == 5


def test_create_reservation_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    reservation = service.create_reservation(
        id_osobe_korisnik=100,
        id_termina=1,
        id_vozila=10,
        kilometraza_vozila=50000,
        opis_problema="   Problem s motorom   ",
        services=_services_payload(),
    )

    assert reservation.Status == ReservationStatus.NA_CEKANJU.value
    assert reservation.OpisProblema == "Problem s motorom"
    assert reservation.IdOsobe_Korisnik == 100
    assert reservation.IdTermina == 1
    assert reservation.IdVozila == 10
    assert len(repository.service_links) == 1
    assert repository.service_links[0].IdUsluge == 1000
    assert repository.service_links[0].Kolicina == 2


def test_create_reservation_fails_when_kilometraza_negative():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=-1,
            opis_problema="opis",
            services=_services_payload(),
        )

    assert error.value.status_code == 400
    assert "Kilometraža" in error.value.detail


def test_create_reservation_fails_when_opis_empty_string():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="",
            services=_services_payload(),
        )

    assert error.value.status_code == 400


def test_create_reservation_fails_when_opis_only_whitespace():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="   ",
            services=_services_payload(),
        )

    assert error.value.status_code == 400


def test_create_reservation_fails_when_services_empty():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="problem",
            services=[],
        )

    assert error.value.status_code == 400


def test_create_reservation_fails_when_quantity_less_than_one():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="problem",
            services=[ReservationServiceItemCreate(IdUsluge=1000, Kolicina=0)],
        )

    assert error.value.status_code == 400
    assert "Količina" in error.value.detail


def test_create_reservation_fails_when_vehicle_does_not_belong_to_customer():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=999,  # different from vehicle owner (100)
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="problem",
            services=_services_payload(),
        )

    assert error.value.status_code == 400
    assert "vozilo" in error.value.detail.lower()


def test_create_reservation_fails_when_appointment_not_free():
    service, _, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.appointments[1].Status = AppointmentStatus.ZAUZET.value

    with pytest.raises(HTTPException) as error:
        service.create_reservation(
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=10000,
            opis_problema="problem",
            services=_services_payload(),
        )

    assert error.value.status_code == 409


def test_approve_reservation_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.approve_reservation(
        reservation_id=1,
        id_osobe_zaposlenik=200,
        komentar="Sve OK",
    )

    assert result.Status == ReservationStatus.ODOBRENA.value
    assert result.IdOsobe_Zaposlenik == 200
    assert result.KomentarZaposlenika == "Sve OK"
    assert 1 in appointment_service.mark_as_occupied_calls


def test_approve_reservation_trims_empty_komentar_to_none():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.approve_reservation(
        reservation_id=1,
        id_osobe_zaposlenik=200,
        komentar="    ",
    )

    assert result.KomentarZaposlenika is None


def test_approve_reservation_conflict_when_appointment_not_free():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.appointments[1].Status = AppointmentStatus.ZAUZET.value
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    with pytest.raises(HTTPException) as error:
        service.approve_reservation(reservation_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409


def test_approve_reservation_conflict_when_another_approved_exists():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    repository.reservations.append(SimpleNamespace(
        IdRezervacije=99,
        Status=ReservationStatus.ODOBRENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    ))
    pending = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(pending)

    with pytest.raises(HTTPException) as error:
        service.approve_reservation(reservation_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "već postoji" in error.value.detail


def test_approve_reservation_conflict_on_invalid_transition():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.ODOBRENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    with pytest.raises(HTTPException) as error:
        service.approve_reservation(reservation_id=1, id_osobe_zaposlenik=200)

    assert error.value.status_code == 409
    assert "Tranzicija" in error.value.detail


def test_reject_reservation_success_does_not_occupy_appointment():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.reject_reservation(
        reservation_id=1,
        id_osobe_zaposlenik=200,
        komentar="nije moguće",
    )

    assert result.Status == ReservationStatus.ODBIJENA.value
    assert result.IdOsobe_Zaposlenik == 200
    assert result.KomentarZaposlenika == "nije moguće"
    assert appointment_service.appointments[1].Status == AppointmentStatus.SLOBODAN.value
    assert appointment_service.mark_as_occupied_calls == []


def test_cancel_reservation_from_pending_keeps_appointment_free():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.cancel_reservation(reservation_id=1)

    assert result.Status == ReservationStatus.OTKAZANA.value
    assert appointment_service.mark_as_free_calls == []


def test_cancel_reservation_from_approved_frees_appointment():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.appointments[1].Status = AppointmentStatus.ZAUZET.value
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.ODOBRENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.cancel_reservation(reservation_id=1)

    assert result.Status == ReservationStatus.OTKAZANA.value
    assert 1 in appointment_service.mark_as_free_calls


def test_cancel_reservation_conflict_from_rejected():
    service, repository, *_ = _make_service()
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.ODBIJENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    with pytest.raises(HTTPException) as error:
        service.cancel_reservation(reservation_id=1)

    assert error.value.status_code == 409


def test_cancel_reservation_conflict_from_completed():
    service, repository, *_ = _make_service()
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.ZAVRSENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    with pytest.raises(HTTPException) as error:
        service.cancel_reservation(reservation_id=1)

    assert error.value.status_code == 409


def test_complete_reservation_success_from_approved():
    service, repository, *_ = _make_service()
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.ODOBRENA.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=200,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    result = service.complete_reservation(reservation_id=1)

    assert result.Status == ReservationStatus.ZAVRSENA.value


def test_complete_reservation_conflict_from_pending():
    service, repository, *_ = _make_service()
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdTermina=1,
        IdOsobe_Zaposlenik=None,
        KomentarZaposlenika=None,
    )
    repository.reservations.append(reservation)

    with pytest.raises(HTTPException) as error:
        service.complete_reservation(reservation_id=1)

    assert error.value.status_code == 409


def _make_pending_reservation(repository, customer_id=100, appointment_id=1, vehicle_id=10):
    reservation = SimpleNamespace(
        IdRezervacije=1,
        Status=ReservationStatus.NA_CEKANJU.value,
        IdOsobe_Korisnik=customer_id,
        IdTermina=appointment_id,
        IdVozila=vehicle_id,
        KilometrazaVozila=50000,
        OpisProblema="old problem",
        KomentarZaposlenika=None,
        IdOsobe_Zaposlenik=None,
    )
    repository.reservations.append(reservation)
    repository.service_links.append(SimpleNamespace(IdRezervacije=1, IdUsluge=1000, Kolicina=1))
    return reservation


def test_update_reservation_header_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.add(2)
    _make_pending_reservation(repository)

    updated = service.update_reservation_header(
        reservation_id=1,
        id_osobe_korisnik=100,
        id_termina=2,
        id_vozila=10,
        kilometraza_vozila=75000,
        opis_problema="  updated problem  ",
    )

    assert updated.IdTermina == 2
    assert updated.KilometrazaVozila == 75000
    assert updated.OpisProblema == "updated problem"


def test_update_reservation_header_fails_when_status_is_not_pending():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    reservation = _make_pending_reservation(repository)
    reservation.Status = ReservationStatus.ODOBRENA.value

    with pytest.raises(HTTPException) as error:
        service.update_reservation_header(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=60000,
            opis_problema="x",
        )

    assert error.value.status_code == 409


def test_update_reservation_header_fails_when_not_owner():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_pending_reservation(repository, customer_id=100)

    with pytest.raises(HTTPException) as error:
        service.update_reservation_header(
            reservation_id=1,
            id_osobe_korisnik=999,
            id_termina=1,
            id_vozila=10,
            kilometraza_vozila=60000,
            opis_problema="x",
        )

    assert error.value.status_code == 403


def test_update_reservation_header_fails_when_new_appointment_not_free():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.add(2, status_value=AppointmentStatus.ZAUZET.value)
    _make_pending_reservation(repository)

    with pytest.raises(HTTPException) as error:
        service.update_reservation_header(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_termina=2,
            id_vozila=10,
            kilometraza_vozila=60000,
            opis_problema="x",
        )

    assert error.value.status_code == 409


def test_update_reservation_header_allows_same_appointment_without_availability_check():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    appointment_service.appointments[1].Status = AppointmentStatus.ZAUZET.value
    _make_pending_reservation(repository)

    updated = service.update_reservation_header(
        reservation_id=1,
        id_osobe_korisnik=100,
        id_termina=1,
        id_vozila=10,
        kilometraza_vozila=80000,
        opis_problema="same slot",
    )

    assert updated.IdTermina == 1
    assert updated.KilometrazaVozila == 80000


def _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=0, minutes_to=60):
    from datetime import time
    appointment = appointment_service.appointments[appointment_id]
    appointment.VrijemeOd = time(hour=minutes_from // 60, minute=minutes_from % 60)
    appointment.VrijemeDo = time(hour=minutes_to // 60, minute=minutes_to % 60)
    return appointment


def _attach_services_relationship(repository, reservation, service_catalog_service):
    """Set up reservation.reservation_services with the catalog so slot capacity check works."""
    reservation.reservation_services = [
        link for link in repository.service_links if link.IdRezervacije == reservation.IdRezervacije
    ]
    # ensure catalog has Trajanje for the linked services
    for link in reservation.reservation_services:
        if link.IdUsluge not in service_catalog_service.services:
            service_catalog_service.add(link.IdUsluge)
        service_catalog_service.services[link.IdUsluge].Trajanje = 30


def test_add_service_to_reservation_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)
    service_catalog_service.add(2000)
    service_catalog_service.services[2000].Trajanje = 20

    link = service.add_service_to_reservation(
        reservation_id=1,
        id_osobe_korisnik=100,
        id_usluge=2000,
        kolicina=1,
    )

    assert link.IdUsluge == 2000
    assert link.Kolicina == 1
    assert any(l.IdUsluge == 2000 for l in repository.service_links)


def test_add_service_to_reservation_rejects_duplicate():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.add_service_to_reservation(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_usluge=1000,
            kolicina=1,
        )

    assert error.value.status_code == 409
    assert "već dodana" in error.value.detail


def test_add_service_to_reservation_rejects_when_slot_exceeded():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)
    service_catalog_service.add(2000)
    service_catalog_service.services[2000].Trajanje = 45

    with pytest.raises(HTTPException) as error:
        service.add_service_to_reservation(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_usluge=2000,
            kolicina=1,
        )

    assert error.value.status_code == 409
    assert "ne stane" in error.value.detail


def test_update_service_quantity_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=10 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)

    link = service.update_service_quantity(
        reservation_id=1,
        id_osobe_korisnik=100,
        id_usluge=1000,
        kolicina=3,
    )

    assert link.Kolicina == 3


def test_update_service_quantity_rejects_when_exceeds_slot():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.update_service_quantity(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_usluge=1000,
            kolicina=5,
        )

    assert error.value.status_code == 409


def test_update_service_quantity_fails_when_service_not_in_reservation():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.update_service_quantity(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_usluge=9999,
            kolicina=1,
        )

    assert error.value.status_code == 404


def test_remove_service_from_reservation_success():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=10 * 60)
    reservation = _make_pending_reservation(repository)
    service_catalog_service.add(2000)
    service_catalog_service.services[2000].Trajanje = 30
    repository.service_links.append(SimpleNamespace(IdRezervacije=1, IdUsluge=2000, Kolicina=1))
    _attach_services_relationship(repository, reservation, service_catalog_service)

    service.remove_service_from_reservation(
        reservation_id=1,
        id_osobe_korisnik=100,
        id_usluge=2000,
    )

    assert not any(l.IdUsluge == 2000 for l in repository.service_links)


def test_remove_service_from_reservation_rejects_when_last_one():
    service, repository, appointment_service, vehicle_service, service_catalog_service = _make_service()
    _setup_world(appointment_service, vehicle_service, service_catalog_service)
    _make_appointment_with_slot(appointment_service, appointment_id=1, minutes_from=8 * 60, minutes_to=9 * 60)
    reservation = _make_pending_reservation(repository)
    _attach_services_relationship(repository, reservation, service_catalog_service)

    with pytest.raises(HTTPException) as error:
        service.remove_service_from_reservation(
            reservation_id=1,
            id_osobe_korisnik=100,
            id_usluge=1000,
        )

    assert error.value.status_code == 409
    assert "barem jednu" in error.value.detail
