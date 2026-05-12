from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app

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


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_function():
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


def test_full_vehicle_flow():
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

    assert create_response.status_code == 201

    created_vehicle = create_response.json()
    vehicle_id = created_vehicle["IdVozila"]

    assert created_vehicle["Marka"] == "Volkswagen"
    assert created_vehicle["Model"] == "Golf"
    assert created_vehicle["IdOsobe"] == customer_id

    get_response = client.get(f"/vehicles/{vehicle_id}")

    assert get_response.status_code == 200

    fetched_vehicle = get_response.json()

    assert fetched_vehicle["IdVozila"] == vehicle_id
    assert fetched_vehicle["RegOznaka"] == "ZG-123-AB"

    list_response = client.get(f"/vehicles/customers/{customer_id}")

    assert list_response.status_code == 200

    customer_vehicles = list_response.json()

    assert len(customer_vehicles) == 1
    assert customer_vehicles[0]["IdVozila"] == vehicle_id

    update_response = client.put(
        f"/vehicles/{vehicle_id}",
        json={
            "Marka": "Volkswagen",
            "Model": "Passat",
            "Godina": 2021,
            "VrstaMotora": "benzin",
            "RegOznaka": "ZG-999-ZZ"
        }
    )

    assert update_response.status_code == 200

    updated_vehicle = update_response.json()

    assert updated_vehicle["IdVozila"] == vehicle_id
    assert updated_vehicle["Model"] == "Passat"
    assert updated_vehicle["Godina"] == 2021
    assert updated_vehicle["RegOznaka"] == "ZG-999-ZZ"

    duplicate_response = client.post(
        "/vehicles",
        json={
            "Marka": "Audi",
            "Model": "A4",
            "Godina": 2020,
            "VrstaMotora": "benzin",
            "RegOznaka": "ZG-999-ZZ",
            "IdOsobe": customer_id
        }
    )

    assert duplicate_response.status_code == 400

    delete_response = client.delete(f"/vehicles/{vehicle_id}")

    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/vehicles/{vehicle_id}")

    assert get_deleted_response.status_code == 404
