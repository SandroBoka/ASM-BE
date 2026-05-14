from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def test_full_customer_flow():
    create_response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ivan",
            "Prezime": "Horvat",
            "Email": "ivan@example.com",
            "Telefon": "091-111-222",
            "Lozinka": "tajna123"
        }
    )

    assert create_response.status_code == 201

    created_customer = create_response.json()
    customer_id = created_customer["IdOsobe"]

    assert created_customer["Ime"] == "Ivan"
    assert created_customer["Prezime"] == "Horvat"
    assert created_customer["Email"] == "ivan@example.com"
    assert "Lozinka" not in created_customer

    list_response = client.get("/persons")

    assert list_response.status_code == 200

    persons = list_response.json()

    assert len(persons) == 1
    assert persons[0]["IdOsobe"] == customer_id
    assert persons[0]["Ime"] == "Ivan"
    assert persons[0]["Prezime"] == "Horvat"
    assert persons[0]["Email"] == "ivan@example.com"
    assert "Lozinka" not in persons[0]

    duplicate_response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ana",
            "Prezime": "Ivic",
            "Email": "ivan@example.com",
            "Telefon": None,
            "Lozinka": "tajna456"
        }
    )

    assert duplicate_response.status_code == 400

    get_response = client.get(f"/persons/customers/{customer_id}")

    assert get_response.status_code == 200

    fetched_customer = get_response.json()

    assert fetched_customer["IdOsobe"] == customer_id
    assert fetched_customer["Email"] == "ivan@example.com"

    update_response = client.put(
        f"/persons/customers/{customer_id}",
        json={
            "Ime": "Ivica",
            "Telefon": "091-999-888"
        }
    )

    assert update_response.status_code == 200

    updated_customer = update_response.json()

    assert updated_customer["IdOsobe"] == customer_id
    assert updated_customer["Ime"] == "Ivica"
    assert updated_customer["Prezime"] == "Horvat"
    assert updated_customer["Telefon"] == "091-999-888"

    delete_response = client.delete(f"/persons/{customer_id}")

    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/persons/customers/{customer_id}")

    assert get_deleted_response.status_code == 404


def test_full_employee_flow():
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

    assert create_response.status_code == 201

    created_employee = create_response.json()
    employee_id = created_employee["IdOsobe"]

    assert created_employee["Ime"] == "Petar"
    assert created_employee["Email"] == "petar@example.com"
    assert created_employee["Uloga"] == "serviser"
    assert "Lozinka" not in created_employee

    list_response = client.get("/persons")

    assert list_response.status_code == 200

    persons = list_response.json()

    assert len(persons) == 1
    assert persons[0]["IdOsobe"] == employee_id
    assert persons[0]["Ime"] == "Petar"
    assert persons[0]["Prezime"] == "Novak"
    assert persons[0]["Email"] == "petar@example.com"
    assert "Lozinka" not in persons[0]

    get_response = client.get(f"/persons/employees/{employee_id}")

    assert get_response.status_code == 200

    fetched_employee = get_response.json()

    assert fetched_employee["IdOsobe"] == employee_id
    assert fetched_employee["Uloga"] == "serviser"

    update_response = client.put(
        f"/persons/employees/{employee_id}",
        json={
            "Prezime": "Kovac",
            "Telefon": "098-555-666",
            "Uloga": "voditelj"
        }
    )

    assert update_response.status_code == 200

    updated_employee = update_response.json()

    assert updated_employee["IdOsobe"] == employee_id
    assert updated_employee["Prezime"] == "Kovac"
    assert updated_employee["Telefon"] == "098-555-666"
    assert updated_employee["Uloga"] == "voditelj"

    role_response = client.patch(
        f"/persons/employees/{employee_id}/role",
        json={"Uloga": "administrator"}
    )

    assert role_response.status_code == 200

    employee_with_new_role = role_response.json()

    assert employee_with_new_role["IdOsobe"] == employee_id
    assert employee_with_new_role["Uloga"] == "administrator"

    delete_response = client.delete(f"/persons/{employee_id}")

    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/persons/employees/{employee_id}")

    assert get_deleted_response.status_code == 404
