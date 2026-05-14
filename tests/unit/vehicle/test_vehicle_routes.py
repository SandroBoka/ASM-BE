from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        TipKorisnika="employee",
        Uloga="admin"
    )


def override_current_customer(person_id: int):
    def _override_get_current_customer():
        return AuthUserResponse(
            IdOsobe=person_id,
            Ime="Ivan",
            Prezime="Horvat",
            Email=f"ivan{person_id}@example.com",
            TipKorisnika=UserType.CUSTOMER,
            Uloga=None
        )

    return _override_get_current_customer


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


def create_customer() -> int:
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

    return response.json()["IdOsobe"]


def test_create_vehicle_api():
    customer_id = create_customer()

    response = client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": customer_id
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdVozila"] is not None
    assert data["Marka"] == "Volkswagen"
    assert data["Model"] == "Golf"
    assert data["Godina"] == 2018
    assert data["VrstaMotora"] == "diesel"
    assert data["RegOznaka"] == "ZG-123-AB"
    assert data["IdOsobe"] == customer_id


def test_customer_cannot_create_vehicle_for_another_customer_api():
    owner_id = create_customer()

    response = client.post(
        "/persons/customers",
        json={
            "Ime": "Ana",
            "Prezime": "Ivic",
            "Email": "ana@example.com",
            "Telefon": None,
            "Lozinka": "tajna456"
        }
    )

    assert response.status_code == 201

    other_customer_id = response.json()["IdOsobe"]
    app.dependency_overrides[get_current_user] = override_current_customer(owner_id)

    response = client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": other_customer_id
        }
    )

    assert response.status_code == 403


def test_get_vehicle_api():
    customer_id = create_customer()

    create_response = client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": customer_id
        }
    )

    vehicle_id = create_response.json()["IdVozila"]

    response = client.get(f"/vehicles/{vehicle_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["IdVozila"] == vehicle_id
    assert data["RegOznaka"] == "ZG-123-AB"


def test_get_customer_vehicles_api():
    customer_id = create_customer()

    client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": customer_id
        }
    )

    client.post(
        "/vehicles",
        json={
            "Marka": "Audi",
            "Model": "A4",
            "Godina": 2020,
            "VrstaMotora": "benzin",
            "RegOznaka": "ZG-456-CD",
            "IdOsobe": customer_id
        }
    )

    response = client.get(f"/vehicles/customers/{customer_id}")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["RegOznaka"] == "ZG-123-AB"
    assert data[1]["RegOznaka"] == "ZG-456-CD"


def test_update_vehicle_api():
    customer_id = create_customer()

    create_response = client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": customer_id
        }
    )

    vehicle_id = create_response.json()["IdVozila"]

    response = client.put(
        f"/vehicles/{vehicle_id}",
        json={
            "Marka": "Volkswagen",
            "Model": "Passat",
            "Godina": 2021,
            "VrstaMotora": "benzin",
            "RegOznaka": "ZG-999-ZZ"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["IdVozila"] == vehicle_id
    assert data["Model"] == "Passat"
    assert data["Godina"] == 2021
    assert data["RegOznaka"] == "ZG-999-ZZ"


def test_delete_vehicle_api():
    customer_id = create_customer()

    create_response = client.post(
        "/vehicles",
        json={
            "Marka": "Volkswagen",
            "Model": "Golf",
            "Godina": 2018,
            "VrstaMotora": "diesel",
            "RegOznaka": "ZG-123-AB",
            "IdOsobe": customer_id
        }
    )

    vehicle_id = create_response.json()["IdVozila"]

    delete_response = client.delete(f"/vehicles/{vehicle_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/vehicles/{vehicle_id}")

    assert get_response.status_code == 404
