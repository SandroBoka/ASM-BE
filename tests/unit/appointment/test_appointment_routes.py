from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.auth_types import UserType
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
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


def override_get_current_user():
    return AuthUserResponse(
        IdOsobe=1,
        Ime="Test",
        Prezime="User",
        Email="test@example.com",
        TipKorisnika=UserType.EMPLOYEE,
        Uloga="admin"
    )


def override_get_current_customer():
    return AuthUserResponse(
        IdOsobe=1,
        Ime="Ivan",
        Prezime="Horvat",
        Email="ivan@example.com",
        TipKorisnika=UserType.CUSTOMER,
        Uloga=None
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_create_appointment_api():
    response = client.post(
        "/appointments",
        json={
            "Datum": "2026-06-01",
            "VrijemeOd": "08:00:00",
            "VrijemeDo": "09:00:00",
            "Status": "slobodan"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdTermina"] is not None
    assert data["Datum"] == "2026-06-01"
    assert data["VrijemeOd"] == "08:00:00"
    assert data["VrijemeDo"] == "09:00:00"
    assert data["Status"] == "slobodan"


def test_customer_cannot_create_appointment_api():
    app.dependency_overrides[get_current_user] = override_get_current_customer

    response = client.post(
        "/appointments",
        json={
            "Datum": "2026-06-01",
            "VrijemeOd": "08:00:00",
            "VrijemeDo": "09:00:00",
            "Status": "slobodan"
        }
    )

    assert response.status_code == 403


def test_get_free_appointments_api():
    client.post(
        "/appointments",
        json={
            "Datum": "2026-06-01",
            "VrijemeOd": "08:00:00",
            "VrijemeDo": "09:00:00",
            "Status": "slobodan"
        }
    )
    client.post(
        "/appointments",
        json={
            "Datum": "2026-06-02",
            "VrijemeOd": "10:00:00",
            "VrijemeDo": "11:00:00",
            "Status": "zauzet"
        }
    )
    app.dependency_overrides[get_current_user] = override_get_current_customer

    response = client.get(
        "/appointments/free?date_from=2026-06-01&date_to=2026-06-30"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["Status"] == "slobodan"
    assert data[0]["Datum"] == "2026-06-01"


def test_get_all_appointments_requires_employee_api():
    app.dependency_overrides[get_current_user] = override_get_current_customer

    response = client.get("/appointments")

    assert response.status_code == 403


def test_update_appointment_api():
    create_response = client.post(
        "/appointments",
        json={
            "Datum": "2026-06-01",
            "VrijemeOd": "08:00:00",
            "VrijemeDo": "09:00:00",
            "Status": "slobodan"
        }
    )
    appointment_id = create_response.json()["IdTermina"]

    response = client.put(
        f"/appointments/{appointment_id}",
        json={
            "Datum": "2026-06-02",
            "VrijemeOd": "10:00:00",
            "VrijemeDo": "11:30:00",
            "Status": "zauzet"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["IdTermina"] == appointment_id
    assert data["Datum"] == "2026-06-02"
    assert data["VrijemeOd"] == "10:00:00"
    assert data["VrijemeDo"] == "11:30:00"
    assert data["Status"] == "zauzet"


def test_delete_appointment_api():
    create_response = client.post(
        "/appointments",
        json={
            "Datum": "2026-06-01",
            "VrijemeOd": "08:00:00",
            "VrijemeDo": "09:00:00",
            "Status": "slobodan"
        }
    )
    appointment_id = create_response.json()["IdTermina"]

    delete_response = client.delete(f"/appointments/{appointment_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/appointments/{appointment_id}")

    assert get_response.status_code == 404
