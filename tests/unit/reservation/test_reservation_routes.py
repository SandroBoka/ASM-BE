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
from app.models.person import Customer, Employee, Person
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


def override_get_current_user():
    return AuthUserResponse(
        IdOsobe=1,
        Ime="Test",
        Prezime="User",
        Email="test@example.com",
        TipKorisnika=UserType.EMPLOYEE,
        Uloga="admin",
    )


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
    """Return a NotificationService backed by FakeEmailService so no real SMTP is hit."""
    db_session = TestingSessionLocal()
    try:
        repository = NotificationRepository(db_session)
        email_service = FakeEmailService()
        yield NotificationService(repository=repository, email_service=email_service)
    finally:
        db_session.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_notification_service] = override_get_notification_service

client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
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


def _seed_vehicle(customer_id: int, reg: str = "ZG-123-AB") -> int:
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


def _create_reservation_via_api(
        customer_id: int,
        appointment_id: int,
        vehicle_id: int,
        service_id: int,
) -> dict:
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.post(
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

    return response.json() if response.status_code == 201 else {}, response


def test_create_reservation_api():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.post(
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

    assert response.status_code == 201

    data = response.json()
    assert data["IdRezervacije"] is not None
    assert data["Status"] == "na cekanju"
    assert data["IdOsobe_Korisnik"] == customer_id
    assert len(data["services"]) == 1
    assert data["services"][0]["Kolicina"] == 1


def test_create_reservation_fails_when_appointment_busy():
    customer_id, vehicle_id, _, service_id = _build_world()
    busy_appointment_id = _seed_appointment(
        vrijeme_od=time(11, 0),
        vrijeme_do=time(12, 0),
        status_value="zauzet",
    )
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.post(
        "/reservations",
        json={
            "IdOsobe_Korisnik": customer_id,
            "IdTermina": busy_appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 50000,
            "OpisProblema": "Cudan zvuk",
            "services": [{"IdUsluge": service_id, "Kolicina": 1}],
        },
    )

    assert response.status_code == 409


def test_get_pending_reservations_api_requires_employee():
    customer_id = _seed_customer()
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)

    response = client.get("/reservations/pending")

    assert response.status_code == 403


def test_get_reservation_for_owner():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    assert create_response.status_code == 201
    reservation_id = create_response.json()["IdRezervacije"]

    # Owner can read
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    get_response = client.get(f"/reservations/{reservation_id}")
    assert get_response.status_code == 200
    assert get_response.json()["IdRezervacije"] == reservation_id

    # Stranger gets 403
    stranger_id = _seed_customer(email="stranger@example.com")
    app.dependency_overrides[get_current_user] = override_current_customer(
        stranger_id, email="stranger@example.com"
    )
    forbidden_response = client.get(f"/reservations/{reservation_id}")
    assert forbidden_response.status_code == 403


def test_update_reservation_header_api():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    assert create_response.status_code == 201
    reservation_id = create_response.json()["IdRezervacije"]

    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    update_response = client.put(
        f"/reservations/{reservation_id}",
        json={
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 60000,
            "OpisProblema": "Novi opis",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()
    assert data["KilometrazaVozila"] == 60000
    assert data["OpisProblema"] == "Novi opis"


def test_update_reservation_header_fails_when_not_owner():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    reservation_id = create_response.json()["IdRezervacije"]

    stranger_id = _seed_customer(email="stranger@example.com")
    app.dependency_overrides[get_current_user] = override_current_customer(
        stranger_id, email="stranger@example.com"
    )

    response = client.put(
        f"/reservations/{reservation_id}",
        json={
            "IdTermina": appointment_id,
            "IdVozila": vehicle_id,
            "KilometrazaVozila": 60000,
            "OpisProblema": "Novi opis",
        },
    )

    assert response.status_code == 403


def test_add_service_to_reservation_api():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    reservation_id = create_response.json()["IdRezervacije"]
    extra_service_id = _seed_service(naziv="Dodatna usluga", trajanje=20)

    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    response = client.post(
        f"/reservations/{reservation_id}/services",
        json={"IdUsluge": extra_service_id, "Kolicina": 1},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["Kolicina"] == 1
    assert data["service"]["IdUsluge"] == extra_service_id


def test_remove_service_from_reservation_api():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    reservation_id = create_response.json()["IdRezervacije"]

    # Add a second service so we can remove one and still have at least one
    extra_service_id = _seed_service(naziv="Dodatna usluga", trajanje=20)
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    add_response = client.post(
        f"/reservations/{reservation_id}/services",
        json={"IdUsluge": extra_service_id, "Kolicina": 1},
    )
    assert add_response.status_code == 201

    delete_response = client.delete(
        f"/reservations/{reservation_id}/services/{extra_service_id}"
    )

    assert delete_response.status_code == 204


def test_approve_reservation_api_requires_employee():
    customer_id, vehicle_id, appointment_id, service_id = _build_world()
    _, create_response = _create_reservation_via_api(
        customer_id, appointment_id, vehicle_id, service_id
    )
    reservation_id = create_response.json()["IdRezervacije"]

    # Customer cannot approve
    app.dependency_overrides[get_current_user] = override_current_customer(customer_id)
    customer_response = client.post(
        f"/reservations/{reservation_id}/approve",
        json={"komentar": None},
    )
    assert customer_response.status_code == 403

    # Employee can approve
    employee_id = _seed_employee()
    app.dependency_overrides[get_current_user] = override_current_employee(employee_id)
    employee_response = client.post(
        f"/reservations/{reservation_id}/approve",
        json={"komentar": "OK"},
    )
    assert employee_response.status_code == 200
    assert employee_response.json()["Status"] == "odobrena"
