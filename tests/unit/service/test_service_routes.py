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


def test_create_service_api():
    response = client.post(
        "/services",
        json={
            "NazivUsluge": "Redovni servis",
            "Opis": "Zamjena ulja i filtera",
            "Trajanje": 60,
            "Cijena": "150.00"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["IdUsluge"] is not None
    assert data["NazivUsluge"] == "Redovni servis"
    assert data["Opis"] == "Zamjena ulja i filtera"
    assert data["Trajanje"] == 60
    assert data["Cijena"] == "150.00"


def test_get_services_api():
    client.post(
        "/services",
        json={
            "NazivUsluge": "Dijagnostika",
            "Opis": "Kompjuterska dijagnostika",
            "Trajanje": 30,
            "Cijena": "50.00"
        }
    )

    response = client.get("/services")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["NazivUsluge"] == "Dijagnostika"


def test_get_service_by_id_api():
    create_response = client.post(
        "/services",
        json={
            "NazivUsluge": "Zamjena guma",
            "Opis": "Sezonska izmjena guma",
            "Trajanje": 45,
            "Cijena": "80.00"
        }
    )

    service_id = create_response.json()["IdUsluge"]

    response = client.get(f"/services/{service_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["IdUsluge"] == service_id
    assert data["NazivUsluge"] == "Zamjena guma"


def test_update_service_api():
    create_response = client.post(
        "/services",
        json={
            "NazivUsluge": "Stari naziv",
            "Opis": "Stari opis",
            "Trajanje": 30,
            "Cijena": "40.00"
        }
    )

    service_id = create_response.json()["IdUsluge"]

    response = client.put(
        f"/services/{service_id}",
        json={
            "NazivUsluge": "Novi naziv",
            "Opis": "Novi opis",
            "Trajanje": 60,
            "Cijena": "100.00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["IdUsluge"] == service_id
    assert data["NazivUsluge"] == "Novi naziv"
    assert data["Opis"] == "Novi opis"
    assert data["Trajanje"] == 60
    assert data["Cijena"] == "100.00"


def test_delete_service_api():
    create_response = client.post(
        "/services",
        json={
            "NazivUsluge": "Za brisanje",
            "Opis": None,
            "Trajanje": 30,
            "Cijena": "20.00"
        }
    )

    service_id = create_response.json()["IdUsluge"]

    delete_response = client.delete(f"/services/{service_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/services/{service_id}")

    assert get_response.status_code == 404


def test_search_services_api():
    client.post(
        "/services",
        json={
            "NazivUsluge": "Redovni servis",
            "Opis": None,
            "Trajanje": 60,
            "Cijena": "150.00"
        }
    )

    client.post(
        "/services",
        json={
            "NazivUsluge": "Dijagnostika",
            "Opis": None,
            "Trajanje": 30,
            "Cijena": "50.00"
        }
    )

    response = client.get("/services?search=servis")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["NazivUsluge"] == "Redovni servis"
