from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.routes.appointment_change_routes import get_notification_service
from app.core.auth_types import UserType
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.appointment import Appointment
from app.models.appointment_change import AppointmentChange
from app.models.notification import Notification
from app.models.person import Customer, Employee, Person
from app.models.reservation import Reservation
from app.models.vehicle import Vehicle
from app.repositories.notification_repository import NotificationRepository
from app.schemas import AuthUserResponse
from app.services.notification_service import NotificationService

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class FakeEmailService:
    def __init__(self):
        self.sent = []

    def send(self, recipient, subject, body):
        self.sent.append({"recipient": recipient, "subject": subject, "body": body})
        return True


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


def override_current_employee(person_id: int, email: str = "emp@example.com"):
    def _override():
        return AuthUserResponse(
            IdOsobe=person_id,
            Ime="Emil",
            Prezime="Zaposleni",
            Email=email,
            TipKorisnika=UserType.EMPLOYEE,
            Uloga="admin",
        )

    return _override


def override_get_notification_service():
    db_session = TestingSessionLocal()
    try:
        repository = NotificationRepository(db_session)
        email_service = FakeEmailService()
        yield NotificationService(repository=repository, email_service=email_service)
    finally:
        db_session.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_notification_service] = override_get_notification_service

client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_notification_service] = override_get_notification_service
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


def _seed_employee(email: str = "emp@example.com") -> int:
    db = TestingSessionLocal()
    try:
        person = Person(
            Ime="Emil",
            Prezime="Zaposleni",
            Email=email,
            Telefon=None,
            Lozinka="hashed",
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        employee = Employee(IdOsobe=person.IdOsobe, Uloga="admin")
        db.add(employee)
        db.commit()
        return person.IdOsobe
    finally:
        db.close()


def _seed_vehicle(customer_id: int) -> int:
    db = TestingSessionLocal()
    try:
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
        return vehicle.IdVozila
    finally:
        db.close()


def _seed_appointment(
        status_value: str,
        appointment_date: date = date(2026, 6, 1),
        vrijeme_od: time = time(8, 0),
        vrijeme_do: time = time(9, 0),
) -> int:
    db = TestingSessionLocal()
    try:
        appointment = Appointment(
            Datum=appointment_date,
            VrijemeOd=vrijeme_od,
            VrijemeDo=vrijeme_do,
            Status=status_value,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment.IdTermina
    finally:
        db.close()


def _seed_reservation(
        customer_id: int,
        appointment_id: int,
        vehicle_id: int,
        status_value: str = "odobrena",
) -> int:
    db = TestingSessionLocal()
    try:
        reservation = Reservation(
            Status=status_value,
            KilometrazaVozila=50000,
            OpisProblema="Problem",
            IdOsobe_Korisnik=customer_id,
            IdTermina=appointment_id,
            IdVozila=vehicle_id,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation.IdRezervacije
    finally:
        db.close()


def _seed_change(
        reservation_id: int,
        old_appointment_id: int,
        new_appointment_id: int,
        status_value: str = "na cekanju",
) -> int:
    db = TestingSessionLocal()
    try:
        change = AppointmentChange(
            Status=status_value,
            IdRezervacije=reservation_id,
            IdStarogTermina=old_appointment_id,
            IdNovogTermina=new_appointment_id,
        )
        db.add(change)
        db.commit()
        db.refresh(change)
        return change.IdZahtjevaPromjene
    finally:
        db.close()


def _build_world():
    customer_id = _seed_customer()
    vehicle_id = _seed_vehicle(customer_id)
    old_appointment_id = _seed_appointment("zauzet")
    new_appointment_id = _seed_appointment(
        "slobodan",
        appointment_date=date(2026, 6, 2),
        vrijeme_od=time(10, 0),
        vrijeme_do=time(11, 0),
    )
    reservation_id = _seed_reservation(
        customer_id,
        old_appointment_id,
        vehicle_id,
    )

    return customer_id, old_appointment_id, new_appointment_id, reservation_id


def test_create_change_request_api():
    customer_id, _, new_appointment_id, reservation_id = _build_world()
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.post(
        "/appointment-changes",
        json={
            "IdRezervacije": reservation_id,
            "IdNovogTermina": new_appointment_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdZahtjevaPromjene"] is not None
    assert data["IdRezervacije"] == reservation_id
    assert data["IdNovogTermina"] == new_appointment_id
    assert data["Status"] == "na cekanju"


def test_customer_cannot_create_change_for_another_customer_api():
    _, _, new_appointment_id, reservation_id = _build_world()
    stranger_id = _seed_customer(email="stranger@example.com")
    app.dependency_overrides[get_current_user] = override_current_customer(
        stranger_id,
        email="stranger@example.com",
    )

    response = client.post(
        "/appointment-changes",
        json={
            "IdRezervacije": reservation_id,
            "IdNovogTermina": new_appointment_id,
        },
    )

    assert response.status_code == 403


def test_get_pending_changes_requires_employee_api():
    customer_id, old_appointment_id, new_appointment_id, reservation_id = _build_world()
    _seed_change(reservation_id, old_appointment_id, new_appointment_id)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.get("/appointment-changes/pending")

    assert response.status_code == 403


def test_get_changes_for_reservation_owner_api():
    customer_id, old_appointment_id, new_appointment_id, reservation_id = _build_world()
    change_id = _seed_change(reservation_id, old_appointment_id, new_appointment_id)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.get(f"/appointment-changes/reservation/{reservation_id}")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["IdZahtjevaPromjene"] == change_id


def test_accept_change_api():
    _, old_appointment_id, new_appointment_id, reservation_id = _build_world()
    employee_id = _seed_employee()
    change_id = _seed_change(reservation_id, old_appointment_id, new_appointment_id)
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)

    response = client.post(
        f"/appointment-changes/{change_id}/accept",
        json={"komentar": "  Moze  "},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["Status"] == "prihvacen"
    assert data["IdOsobe_Zaposlenik"] == employee_id
    assert data["KomentarZaposlenika"] == "Moze"


def test_reject_change_api():
    _, old_appointment_id, new_appointment_id, reservation_id = _build_world()
    employee_id = _seed_employee()
    change_id = _seed_change(reservation_id, old_appointment_id, new_appointment_id)
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)

    response = client.post(
        f"/appointment-changes/{change_id}/reject",
        json={"komentar": "Nije moguce"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["Status"] == "odbijen"
    assert data["IdOsobe_Zaposlenik"] == employee_id
    assert data["KomentarZaposlenika"] == "Nije moguce"


def test_accept_change_creates_notification_api():
    customer_id, old_appointment_id, new_appointment_id, reservation_id = _build_world()
    employee_id = _seed_employee()
    change_id = _seed_change(reservation_id, old_appointment_id, new_appointment_id)
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)

    response = client.post(
        f"/appointment-changes/{change_id}/accept",
        json={},
    )

    assert response.status_code == 200

    db = TestingSessionLocal()
    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.IdOsobe == customer_id)  # type: ignore[arg-type]
            .all()
        )

        assert len(notifications) == 1
        assert notifications[0].Naslov == "Zahtjev za promjenu termina prihvaćen"
    finally:
        db.close()
