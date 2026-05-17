from datetime import date, time
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.statuses import AppointmentStatus, ReservationStatus
from app.db.database import Base
from app.models.appointment import Appointment
from app.models.person import Customer, Person
from app.models.reservation import Reservation
from app.models.reservation_service import ReservationService as ReservationServiceLink
from app.models.service import Service
from app.models.vehicle import Vehicle
from app.repositories.reservation_repository import ReservationRepository

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _create_person(db, email="ivan@example.com", ime="Ivan", prezime="Horvat") -> Person:
    person = Person(
        Ime=ime,
        Prezime=prezime,
        Email=email,
        Telefon="091-111-222",
        Lozinka="hashed-password"
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def _create_customer(db, email="ivan@example.com") -> Customer:
    person = _create_person(db, email=email)
    customer = Customer(IdOsobe=person.IdOsobe)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def _create_vehicle(db, id_osobe: int, reg: str = "ZG-123-AB") -> Vehicle:
    vehicle = Vehicle(
        Marka="Volkswagen",
        Model="Golf",
        Godina=2018,
        VrstaMotora="diesel",
        RegOznaka=reg,
        IdOsobe=id_osobe
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def _create_appointment(
        db,
        status_value: str = AppointmentStatus.SLOBODAN.value,
        datum: date | None = None,
        vrijeme_od: time | None = None,
        vrijeme_do: time | None = None,
) -> Appointment:
    appointment = Appointment(
        Datum=datum or date(2026, 6, 1),
        VrijemeOd=vrijeme_od or time(8, 0),
        VrijemeDo=vrijeme_do or time(9, 0),
        Status=status_value
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def _create_service(db, naziv: str = "Redovni servis", trajanje: int = 30) -> Service:
    service = Service(
        NazivUsluge=naziv,
        Opis="Test opis",
        Trajanje=trajanje,
        Cijena=Decimal("100.00")
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def _build_world(db):
    customer = _create_customer(db)
    vehicle = _create_vehicle(db, customer.IdOsobe)
    appointment = _create_appointment(db)
    service = _create_service(db)
    return customer, vehicle, appointment, service


def _build_reservation(
        customer_id: int,
        appointment_id: int,
        vehicle_id: int,
        status_value: str = ReservationStatus.NA_CEKANJU.value,
        opis: str = "Cudan zvuk",
) -> Reservation:
    return Reservation(
        Status=status_value,
        KilometrazaVozila=50000,
        OpisProblema=opis,
        IdOsobe_Korisnik=customer_id,
        IdTermina=appointment_id,
        IdVozila=vehicle_id,
    )


def test_create_reservation_persists():
    db = TestingSessionLocal()
    customer, vehicle, appointment, _ = _build_world(db)
    repository = ReservationRepository(db)

    reservation = repository.create(
        _build_reservation(customer.IdOsobe, appointment.IdTermina, vehicle.IdVozila)
    )

    assert reservation.IdRezervacije is not None
    assert reservation.Status == ReservationStatus.NA_CEKANJU.value

    rows = db.query(Reservation).all()

    assert len(rows) == 1
    assert rows[0].IdRezervacije == reservation.IdRezervacije

    db.close()


def test_get_by_id_returns_match():
    db = TestingSessionLocal()
    customer, vehicle, appointment, _ = _build_world(db)
    repository = ReservationRepository(db)
    created = repository.create(
        _build_reservation(customer.IdOsobe, appointment.IdTermina, vehicle.IdVozila)
    )

    found = repository.get_by_id(created.IdRezervacije)

    assert found is not None
    assert found.IdRezervacije == created.IdRezervacije
    assert found.OpisProblema == "Cudan zvuk"

    db.close()


def test_get_by_id_returns_none_when_missing():
    db = TestingSessionLocal()
    repository = ReservationRepository(db)

    found = repository.get_by_id(9999)

    assert found is None

    db.close()


def test_get_by_customer_id_returns_only_owned():
    db = TestingSessionLocal()
    owner = _create_customer(db, email="owner@example.com")
    other = _create_customer(db, email="other@example.com")

    owner_vehicle = _create_vehicle(db, owner.IdOsobe, reg="ZG-OWN-1")
    other_vehicle = _create_vehicle(db, other.IdOsobe, reg="ZG-OTH-1")

    appointment_one = _create_appointment(db)
    appointment_two = _create_appointment(
        db,
        vrijeme_od=time(10, 0),
        vrijeme_do=time(11, 0),
    )

    repository = ReservationRepository(db)
    owner_reservation = repository.create(
        _build_reservation(owner.IdOsobe, appointment_one.IdTermina, owner_vehicle.IdVozila)
    )
    repository.create(
        _build_reservation(other.IdOsobe, appointment_two.IdTermina, other_vehicle.IdVozila)
    )

    owner_reservations = repository.get_by_customer_id(owner.IdOsobe)

    assert len(owner_reservations) == 1
    assert owner_reservations[0].IdRezervacije == owner_reservation.IdRezervacije
    assert owner_reservations[0].IdOsobe_Korisnik == owner.IdOsobe

    db.close()


def test_get_by_status_filters_correctly():
    db = TestingSessionLocal()
    customer, vehicle, appointment, _ = _build_world(db)
    appointment_two = _create_appointment(
        db,
        vrijeme_od=time(10, 0),
        vrijeme_do=time(11, 0),
    )
    repository = ReservationRepository(db)

    pending = repository.create(_build_reservation(
        customer.IdOsobe,
        appointment.IdTermina,
        vehicle.IdVozila,
        status_value=ReservationStatus.NA_CEKANJU.value,
    ))
    repository.create(_build_reservation(
        customer.IdOsobe,
        appointment_two.IdTermina,
        vehicle.IdVozila,
        status_value=ReservationStatus.ODOBRENA.value,
        opis="approved",
    ))

    pending_rows = repository.get_by_status(ReservationStatus.NA_CEKANJU.value)
    approved_rows = repository.get_by_status(ReservationStatus.ODOBRENA.value)

    assert len(pending_rows) == 1
    assert pending_rows[0].IdRezervacije == pending.IdRezervacije
    assert len(approved_rows) == 1
    assert approved_rows[0].Status == ReservationStatus.ODOBRENA.value

    db.close()


def test_get_approved_by_appointment_id_returns_only_approved():
    db = TestingSessionLocal()
    customer, vehicle, appointment, _ = _build_world(db)
    repository = ReservationRepository(db)

    pending_reservation = repository.create(_build_reservation(
        customer.IdOsobe,
        appointment.IdTermina,
        vehicle.IdVozila,
        status_value=ReservationStatus.NA_CEKANJU.value,
    ))

    no_match = repository.get_approved_by_appointment_id(appointment.IdTermina)

    assert no_match is None

    pending_reservation.Status = ReservationStatus.ODOBRENA.value
    db.commit()
    db.refresh(pending_reservation)

    approved = repository.get_approved_by_appointment_id(appointment.IdTermina)

    assert approved is not None
    assert approved.IdRezervacije == pending_reservation.IdRezervacije
    assert approved.Status == ReservationStatus.ODOBRENA.value

    db.close()


def test_add_service_and_delete_services():
    db = TestingSessionLocal()
    customer, vehicle, appointment, service = _build_world(db)
    other_service = _create_service(db, naziv="Veliki servis", trajanje=20)
    repository = ReservationRepository(db)

    reservation = repository.create(
        _build_reservation(customer.IdOsobe, appointment.IdTermina, vehicle.IdVozila)
    )

    link_one = repository.add_service(ReservationServiceLink(
        IdRezervacije=reservation.IdRezervacije,
        IdUsluge=service.IdUsluge,
        Kolicina=2,
    ))
    link_two = repository.add_service(ReservationServiceLink(
        IdRezervacije=reservation.IdRezervacije,
        IdUsluge=other_service.IdUsluge,
        Kolicina=1,
    ))

    assert link_one.Kolicina == 2
    assert link_two.Kolicina == 1

    all_links = db.query(ReservationServiceLink).all()
    assert len(all_links) == 2

    repository.delete_services(reservation.IdRezervacije)

    remaining = db.query(ReservationServiceLink).all()
    assert remaining == []

    db.close()


def test_get_service_link_and_delete_service_link():
    db = TestingSessionLocal()
    customer, vehicle, appointment, service = _build_world(db)
    repository = ReservationRepository(db)

    reservation = repository.create(
        _build_reservation(customer.IdOsobe, appointment.IdTermina, vehicle.IdVozila)
    )
    repository.add_service(ReservationServiceLink(
        IdRezervacije=reservation.IdRezervacije,
        IdUsluge=service.IdUsluge,
        Kolicina=3,
    ))

    fetched_link = repository.get_service_link(reservation.IdRezervacije, service.IdUsluge)

    assert fetched_link is not None
    assert fetched_link.Kolicina == 3

    missing_link = repository.get_service_link(reservation.IdRezervacije, 9999)
    assert missing_link is None

    repository.delete_service_link(fetched_link)

    after_delete = repository.get_service_link(reservation.IdRezervacije, service.IdUsluge)
    assert after_delete is None

    db.close()
