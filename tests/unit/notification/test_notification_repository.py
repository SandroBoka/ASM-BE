from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.db.database import Base
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.person import Customer, Person
from app.models.reservation import Reservation
from app.models.vehicle import Vehicle
from app.repositories.notification_repository import NotificationRepository

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


def create_reservation(db, email: str = "ivan@example.com") -> Reservation:
    person = Person(
        Ime="Ivan",
        Prezime="Horvat",
        Email=email,
        Telefon=None,
        Lozinka="hashed",
    )
    db.add(person)
    db.commit()
    db.refresh(person)

    customer = Customer(IdOsobe=person.IdOsobe)
    db.add(customer)

    appointment = Appointment(
        Datum=date(2026, 6, 1),
        VrijemeOd=time(8, 0),
        VrijemeDo=time(9, 0),
        Status="slobodan",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    vehicle = Vehicle(
        Marka="Volkswagen",
        Model="Golf",
        Godina=2018,
        VrstaMotora="diesel",
        RegOznaka=f"ZG-{person.IdOsobe:03d}-AB",
        IdOsobe=person.IdOsobe,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    reservation = Reservation(
        Status="na cekanju",
        KilometrazaVozila=50000,
        OpisProblema="Problem",
        IdOsobe_Korisnik=person.IdOsobe,
        IdTermina=appointment.IdTermina,
        IdVozila=vehicle.IdVozila,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def create_notification(
        repository: NotificationRepository,
        reservation: Reservation,
        title: str = "Rezervacija zaprimljena",
        read: bool = False,
) -> Notification:
    return repository.create(Notification(
        Naslov=title,
        Tekst="Tekst obavijesti",
        IdOsobe=reservation.IdOsobe_Korisnik,
        IdRezervacije=reservation.IdRezervacije,
        Procitana=read,
    ))


def test_create_notification_in_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)

    notification = create_notification(repository, reservation)

    assert notification.IdObavijesti is not None
    assert notification.DatumSlanja is not None
    assert notification.Procitana is False
    assert notification.IdOsobe == reservation.IdOsobe_Korisnik

    db.close()


def test_get_notification_by_id_from_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)
    notification = create_notification(repository, reservation)

    found_notification = repository.get_by_id(notification.IdObavijesti)

    assert found_notification is not None
    assert found_notification.IdObavijesti == notification.IdObavijesti

    db.close()


def test_get_notifications_by_customer_id_from_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    first_reservation = create_reservation(db, email="ivan@example.com")
    second_reservation = create_reservation(db, email="ana@example.com")
    first_notification = create_notification(repository, first_reservation)
    second_notification = create_notification(repository, second_reservation)

    notifications = repository.get_by_customer_id(first_reservation.IdOsobe_Korisnik)

    assert first_notification in notifications
    assert second_notification not in notifications

    db.close()


def test_get_notifications_by_reservation_id_from_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)
    notification = create_notification(repository, reservation)

    notifications = repository.get_by_reservation_id(reservation.IdRezervacije)

    assert [item.IdObavijesti for item in notifications] == [
        notification.IdObavijesti
    ]

    db.close()


def test_get_unread_notifications_by_customer_id_from_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)
    unread = create_notification(repository, reservation, read=False)
    read = create_notification(repository, reservation, title="Procitana", read=True)

    notifications = repository.get_unread_by_customer_id(
        reservation.IdOsobe_Korisnik
    )

    assert unread in notifications
    assert read not in notifications

    db.close()


def test_update_notification_in_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)
    notification = create_notification(repository, reservation)

    notification.Procitana = True

    updated_notification = repository.update(notification)

    assert updated_notification.Procitana is True

    db.close()


def test_delete_notification_from_database():
    db = TestingSessionLocal()
    repository = NotificationRepository(db)
    reservation = create_reservation(db)
    notification = create_notification(repository, reservation)
    notification_id = notification.IdObavijesti

    repository.delete(notification)

    deleted_notification = repository.get_by_id(notification_id)

    assert deleted_notification is None

    db.close()
