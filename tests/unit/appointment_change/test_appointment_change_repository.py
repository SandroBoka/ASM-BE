from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.db.database import Base
from app.models.appointment import Appointment
from app.models.appointment_change import AppointmentChange
from app.models.person import Customer, Person
from app.models.reservation import Reservation
from app.models.vehicle import Vehicle
from app.repositories.appointment_change_repository import AppointmentChangeRepository

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


def create_customer(db) -> Customer:
    person = Person(
        Ime="Ivan",
        Prezime="Horvat",
        Email="ivan@example.com",
        Telefon=None,
        Lozinka="hashed",
    )
    db.add(person)
    db.commit()
    db.refresh(person)

    customer = Customer(IdOsobe=person.IdOsobe)
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_appointment(
        db,
        appointment_date: date = date(2026, 6, 1),
        vrijeme_od: time = time(8, 0),
        vrijeme_do: time = time(9, 0),
        status_value: str = "slobodan",
) -> Appointment:
    appointment = Appointment(
        Datum=appointment_date,
        VrijemeOd=vrijeme_od,
        VrijemeDo=vrijeme_do,
        Status=status_value,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def create_reservation(db, customer_id: int, appointment_id: int) -> Reservation:
    vehicle = Vehicle(
        Marka="Volkswagen",
        Model="Golf",
        Godina=2018,
        VrstaMotora="diesel",
        RegOznaka="ZG-123-AB",
        IdOsobe=customer_id,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    reservation = Reservation(
        Status="odobrena",
        KilometrazaVozila=50000,
        OpisProblema="Problem",
        IdOsobe_Korisnik=customer_id,
        IdTermina=appointment_id,
        IdVozila=vehicle.IdVozila,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def create_change(
        repository: AppointmentChangeRepository,
        reservation_id: int,
        old_appointment_id: int,
        new_appointment_id: int,
        status_value: str = "na cekanju",
) -> AppointmentChange:
    return repository.create(AppointmentChange(
        Status=status_value,
        IdRezervacije=reservation_id,
        IdStarogTermina=old_appointment_id,
        IdNovogTermina=new_appointment_id,
    ))


def seed_world(db):
    customer = create_customer(db)
    old_appointment = create_appointment(db, status_value="zauzet")
    new_appointment = create_appointment(
        db,
        appointment_date=date(2026, 6, 2),
        status_value="slobodan",
    )
    reservation = create_reservation(
        db,
        customer_id=customer.IdOsobe,
        appointment_id=old_appointment.IdTermina,
    )

    return customer, old_appointment, new_appointment, reservation


def test_create_appointment_change_in_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)

    change = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
    )

    assert change.IdZahtjevaPromjene is not None
    assert change.DatumZahtjeva is not None
    assert change.Status == "na cekanju"

    db.close()


def test_get_appointment_change_by_id_from_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)
    change = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
    )

    found_change = repository.get_by_id(change.IdZahtjevaPromjene)

    assert found_change is not None
    assert found_change.IdZahtjevaPromjene == change.IdZahtjevaPromjene

    db.close()


def test_get_appointment_changes_by_reservation_id_from_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)
    change = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
    )

    changes = repository.get_by_reservation_id(reservation.IdRezervacije)

    assert [item.IdZahtjevaPromjene for item in changes] == [
        change.IdZahtjevaPromjene
    ]

    db.close()


def test_get_appointment_changes_by_status_from_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)
    pending = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
        status_value="na cekanju",
    )
    rejected = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
        status_value="odbijen",
    )

    changes = repository.get_by_status("na cekanju")

    assert pending in changes
    assert rejected not in changes

    db.close()


def test_update_appointment_change_in_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)
    change = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
    )

    change.Status = "odbijen"
    change.KomentarZaposlenika = "Nije moguce"

    updated_change = repository.update(change)

    assert updated_change.Status == "odbijen"
    assert updated_change.KomentarZaposlenika == "Nije moguce"

    db.close()


def test_delete_appointment_change_from_database():
    db = TestingSessionLocal()
    repository = AppointmentChangeRepository(db)
    _, old_appointment, new_appointment, reservation = seed_world(db)
    change = create_change(
        repository,
        reservation.IdRezervacije,
        old_appointment.IdTermina,
        new_appointment.IdTermina,
    )
    change_id = change.IdZahtjevaPromjene

    repository.delete(change)

    deleted_change = repository.get_by_id(change_id)

    assert deleted_change is None

    db.close()
