from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
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
        TipKorisnika="employee",
        Uloga="admin"
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


def test_get_all_persons_api():
    first_response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ivan",
            "Prezime": "Horvat",
            "Email": "ivan@example.com",
            "Telefon": "091-111-222",
            "Lozinka": "tajna123"
        }
    )

    second_response = client.post(
        "/persons/employees",
        json={
            "Ime": "Petar",
            "Prezime": "Novak",
            "Email": "petar@example.com",
            "Telefon": None,
            "Lozinka": "tajna456",
            "Uloga": "serviser"
        }
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get("/persons")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["Ime"] == "Ivan"
    assert data[0]["Email"] == "ivan@example.com"
    assert "Lozinka" not in data[0]
    assert data[1]["Ime"] == "Petar"
    assert data[1]["Email"] == "petar@example.com"
    assert "Lozinka" not in data[1]


def test_create_customer_api():
    response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ivan",
            "Prezime": "Horvat",
            "Email": "ivan@example.com",
            "Telefon": "091-111-222",
            "Lozinka": "tajna123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdOsobe"] is not None
    assert data["Ime"] == "Ivan"
    assert data["Email"] == "ivan@example.com"
    assert "Lozinka" not in data


def test_create_employee_api():
    response = client.post(
        "/persons/employees",
        json={
            "Ime": "Petar",
            "Prezime": "Novak",
            "Email": "petar@example.com",
            "Telefon": None,
            "Lozinka": "tajna123",
            "Uloga": "serviser"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdOsobe"] is not None
    assert data["Email"] == "petar@example.com"
    assert data["Uloga"] == "serviser"
    assert "Lozinka" not in data


def test_update_customer_api():
    create_response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ivan",
            "Prezime": "Horvat",
            "Email": "ivan@example.com",
            "Telefon": None,
            "Lozinka": "tajna123"
        }
    )

    customer_id = create_response.json()["IdOsobe"]

    response = client.put(
        f"/persons/customers/{customer_id}",
        json={
            "Ime": "Ivica",
            "Telefon": "091-999-888"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["IdOsobe"] == customer_id
    assert data["Ime"] == "Ivica"
    assert data["Telefon"] == "091-999-888"


def test_update_employee_role_api():
    create_response = client.post(
        "/persons/employees",
        json={
            "Ime": "Petar",
            "Prezime": "Novak",
            "Email": "petar@example.com",
            "Telefon": None,
            "Lozinka": "tajna123",
            "Uloga": "serviser"
        }
    )

    employee_id = create_response.json()["IdOsobe"]

    response = client.patch(
        f"/persons/employees/{employee_id}/role",
        json={"Uloga": "voditelj"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["IdOsobe"] == employee_id
    assert data["Uloga"] == "voditelj"
