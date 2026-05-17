from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.auth_types import UserType
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.person import Customer, Person
from app.models.reservation import Reservation
from app.models.vehicle import Vehicle
from app.schemas import AuthUserResponse

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_current_customer(person_id: int, email: str = "ivan@example.com"):
    def _override():
        return AuthUserResponse(
            IdOsobe=person_id,
            Ime="Ivan",
            Prezime="Horvat",
            Email=email,
            TipKorisnika=UserType.CUSTOMER,
            Uloga=None,
        )

    return _override


def override_current_employee():
    return AuthUserResponse(
        IdOsobe=1,
        Ime="Emil",
        Prezime="Zaposleni",
        Email="emp@example.com",
        TipKorisnika=UserType.EMPLOYEE,
        Uloga="admin",
    )


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _seed_customer(email: str = "ivan@example.com") -> int:
    db = TestingSessionLocal()
    try:
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
        db.commit()
        return person.IdOsobe
    finally:
        db.close()


def _seed_reservation(customer_id: int) -> int:
    db = TestingSessionLocal()
    try:
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
            RegOznaka=f"ZG-{customer_id:03d}-AB",
            IdOsobe=customer_id,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        reservation = Reservation(
            Status="na cekanju",
            KilometrazaVozila=50000,
            OpisProblema="Problem",
            IdOsobe_Korisnik=customer_id,
            IdTermina=appointment.IdTermina,
            IdVozila=vehicle.IdVozila,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation.IdRezervacije
    finally:
        db.close()


def _seed_notification(
        customer_id: int,
        reservation_id: int,
        title: str = "Rezervacija zaprimljena",
        read: bool = False,
) -> int:
    db = TestingSessionLocal()
    try:
        notification = Notification(
            Naslov=title,
            Tekst="Tekst obavijesti",
            IdOsobe=customer_id,
            IdRezervacije=reservation_id,
            Procitana=read,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification.IdObavijesti
    finally:
        db.close()


def _seed_world():
    customer_id = _seed_customer()
    reservation_id = _seed_reservation(customer_id)
    return customer_id, reservation_id


def test_get_my_notifications_api():
    customer_id, reservation_id = _seed_world()
    _seed_notification(customer_id, reservation_id)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.get("/notifications")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["Naslov"] == "Rezervacija zaprimljena"
    assert data[0]["IdOsobe"] == customer_id


def test_get_my_unread_notifications_api():
    customer_id, reservation_id = _seed_world()
    unread_id = _seed_notification(customer_id, reservation_id, read=False)
    _seed_notification(customer_id, reservation_id, title="Procitana", read=True)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.get("/notifications/unread")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["IdObavijesti"] == unread_id
    assert data[0]["Procitana"] is False


def test_mark_notification_as_read_api():
    customer_id, reservation_id = _seed_world()
    notification_id = _seed_notification(customer_id, reservation_id, read=False)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.post(f"/notifications/{notification_id}/read")

    assert response.status_code == 200

    data = response.json()

    assert data["IdObavijesti"] == notification_id
    assert data["Procitana"] is True


def test_customer_cannot_mark_other_customer_notification_as_read_api():
    customer_id, reservation_id = _seed_world()
    notification_id = _seed_notification(customer_id, reservation_id, read=False)
    stranger_id = _seed_customer(email="stranger@example.com")
    app.dependency_overrides[get_current_user] = override_current_customer(
        stranger_id,
        email="stranger@example.com",
    )

    response = client.post(f"/notifications/{notification_id}/read")

    assert response.status_code == 403


def test_employee_cannot_read_customer_notifications_api():
    customer_id, reservation_id = _seed_world()
    _seed_notification(customer_id, reservation_id)
    app.dependency_overrides[get_current_user] = override_current_employee

    response = client.get("/notifications")

    assert response.status_code == 403
