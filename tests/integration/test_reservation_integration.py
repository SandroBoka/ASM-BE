from datetime import date, time
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.routes.reservation_routes import get_notification_service
from app.core.auth_types import UserType
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.person import Customer, Employee, Person
from app.models.reservation import Reservation
from app.models.service import Service
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
    app.dependency_overrides.pop(get_current_user, None)


def _seed_customer(email: str = "ivan@example.com") -> int:
    db = TestingSessionLocal()
    try:
        person = Person(
            Ime="Ivan",
            Prezime="Horvat",
            Email=email,
            Telefon="091-111-222",
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


def _seed_employee(email: str = "emp@example.com", uloga: str = "admin") -> int:
    db = TestingSessionLocal()
    try:
        person = Person(
            Ime="Emil",
            Prezime="Zaposleni",
            Email=email,
            Telefon="091-999-888",
            Lozinka="hashed",
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        employee = Employee(IdOsobe=person.IdOsobe, Uloga=uloga)
        db.add(employee)
        db.commit()
        return person.IdOsobe
    finally:
        db.close()


def _seed_vehicle(customer_id: int, reg: str = "ZG-INT-AB") -> int:
    db = TestingSessionLocal()
    try:
        vehicle = Vehicle(
            Marka="Volkswagen",
            Model="Golf",
            Godina=2018,
            VrstaMotora="diesel",
            RegOznaka=reg,
            IdOsobe=customer_id,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return vehicle.IdVozila
    finally:
        db.close()


def _seed_appointment(
        datum: date | None = None,
        vrijeme_od: time | None = None,
        vrijeme_do: time | None = None,
        status_value: str = "slobodan",
) -> int:
    db = TestingSessionLocal()
    try:
        appointment = Appointment(
            Datum=datum or date(2026, 6, 1),
            VrijemeOd=vrijeme_od or time(8, 0),
            VrijemeDo=vrijeme_do or time(10, 0),
            Status=status_value,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment.IdTermina
    finally:
        db.close()


def _seed_service(naziv: str = "Redovni servis", trajanje: int = 30) -> int:
    db = TestingSessionLocal()
    try:
        service = Service(
            NazivUsluge=naziv,
            Opis="Test",
            Trajanje=trajanje,
            Cijena=Decimal("100.00"),
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        return service.IdUsluge
    finally:
        db.close()


def _build_world():
    customer_id = _seed_customer()
    vehicle_id = _seed_vehicle(customer_id)
    appointment_id = _seed_appointment()
    service_id = _seed_service()
    return customer_id, vehicle_id, appointment_id, service_id


def test_full_reservation_flow_customer_creates_and_employee_approves():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    employee_id = _seed_employee()

    # Customer creates the reservation
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    create_response = client.post(
        "/reservations",
        json={
            "IdOsobe_Korisnik": customer_id,
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 50000,
            "OpisProblema": "Cudan zvuk",
            "services": [{"IdUsluge": service_id, "Kolicina": 1}],
        },
    )

    assert create_response.status_code == 201
    reservation_id = create_response.json()["IdRezervacije"]

    # Employee approves
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)
    approve_response = client.post(
        f"/reservations/{reservation_id}/approve",
        json={"komentar": "Sve OK"},
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["Status"] == "odobrena"
    assert approved["IdOsobe_Zaposlenik"] == employee_id

    # Verify DB state
    db = TestingSessionLocal()
    try:
        reservation_row = db.query(Reservation).filter(
            Reservation.IdRezervacije == reservation_id
        ).first()
        assert reservation_row is not None
        assert reservation_row.Status == "odobrena"
        assert reservation_row.IdOsobe_Zaposlenik == employee_id

        appointment_row = db.query(Appointment).filter(
            Appointment.IdTermina == appointment_id
        ).first()
        assert appointment_row is not None
        assert appointment_row.Status == "zauzet"

        notifications = db.query(Notification).filter(
            Notification.IdRezervacije == reservation_id
        ).all()
        assert len(notifications) == 2
        titles = sorted([n.Naslov for n in notifications])
        assert "Rezervacija odobrena" in titles
        assert "Rezervacija zaprimljena" in titles
    finally:
        db.close()


def test_full_reservation_flow_customer_edits_then_employee_rejects():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    employee_id = _seed_employee()
    extra_service_id = _seed_service(naziv="Dodatna usluga", trajanje=20)

    # Customer creates
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    create_response = client.post(
        "/reservations",
        json={
            "IdOsobe_Korisnik": customer_id,
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 50000,
            "OpisProblema": "Cudan zvuk",
            "services": [{"IdUsluge": service_id, "Kolicina": 1}],
        },
    )
    assert create_response.status_code == 201
    reservation_id = create_response.json()["IdRezervacije"]

    # Customer edits header (PUT)
    put_response = client.put(
        f"/reservations/{reservation_id}",
        json={
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 60000,
            "OpisProblema": "Auzuriran opis",
        },
    )
    assert put_response.status_code == 200
    assert put_response.json()["KilometrazaVozila"] == 60000

    # Customer adds a service
    add_response = client.post(
        f"/reservations/{reservation_id}/services",
        json={"IdUsluge": extra_service_id, "Kolicina": 1},
    )
    assert add_response.status_code == 201

    # Customer changes the quantity of the original service
    quantity_response = client.put(
        f"/reservations/{reservation_id}/services/{service_id}",
        json={"Kolicina": 2},
    )
    assert quantity_response.status_code == 200
    assert quantity_response.json()["Kolicina"] == 2

    # Customer removes the extra service
    delete_response = client.delete(
        f"/reservations/{reservation_id}/services/{extra_service_id}"
    )
    assert delete_response.status_code == 204

    # Employee rejects
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)
    reject_response = client.post(
        f"/reservations/{reservation_id}/reject",
        json={"komentar": "Nije moguce"},
    )
    assert reject_response.status_code == 200
    rejected = reject_response.json()
    assert rejected["Status"] == "odbijena"

    # Verify DB: appointment stays free
    db = TestingSessionLocal()
    try:
        appointment_row = db.query(Appointment).filter(
            Appointment.IdTermina == appointment_id
        ).first()
        assert appointment_row is not None
        assert appointment_row.Status == "slobodan"
    finally:
        db.close()


def test_reservation_cancel_releases_appointment_and_notifies():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    employee_id = _seed_employee()

    # Customer creates
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    create_response = client.post(
        "/reservations",
        json={
            "IdOsobe_Korisnik": customer_id,
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 50000,
            "OpisProblema": "Cudan zvuk",
            "services": [{"IdUsluge": service_id, "Kolicina": 1}],
        },
    )
    assert create_response.status_code == 201
    reservation_id = create_response.json()["IdRezervacije"]

    # Employee approves
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)
    approve_response = client.post(
        f"/reservations/{reservation_id}/approve",
        json={"komentar": None},
    )
    assert approve_response.status_code == 200

    # Verify appointment is occupied
    db = TestingSessionLocal()
    try:
        appointment_row = db.query(Appointment).filter(
            Appointment.IdTermina == appointment_id
        ).first()
        assert appointment_row.Status == "zauzet"
    finally:
        db.close()

    # Customer cancels
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    cancel_response = client.post(
        f"/reservations/{reservation_id}/cancel",
        json={"komentar": "Prebacujem"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["Status"] == "otkazana"

    # Verify appointment is free again and notification was created
    db = TestingSessionLocal()
    try:
        appointment_row = db.query(Appointment).filter(
            Appointment.IdTermina == appointment_id
        ).first()
        assert appointment_row.Status == "slobodan"

        notifications = db.query(Notification).filter(
            Notification.IdRezervacije == reservation_id
        ).all()
        titles = [n.Naslov for n in notifications]
        assert "Rezervacija otkazana" in titles
    finally:
        db.close()
