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


def test_full_service_crud_flow():
    create_response = client.post(
        "/services",
        json={
            "NazivUsluge": "Redovni servis",
            "Opis": "Zamjena ulja i filtera",
            "Trajanje": 60,
            "Cijena": "150.00"
        }
    )

    assert create_response.status_code == 201

    created_service = create_response.json()

    service_id = created_service["IdUsluge"]

    get_response = client.get(f"/services/{service_id}")

    assert get_response.status_code == 200

    fetched_service = get_response.json()

    assert fetched_service["NazivUsluge"] == "Redovni servis"
    assert fetched_service["Trajanje"] == 60

    update_response = client.put(
        f"/services/{service_id}",
        json={
            "NazivUsluge": "Veliki servis",
            "Opis": "Zamjena remena i filtera",
            "Trajanje": 120,
            "Cijena": "350.00"
        }
    )

    assert update_response.status_code == 200

    updated_service = update_response.json()

    assert updated_service["NazivUsluge"] == "Veliki servis"
    assert updated_service["Trajanje"] == 120
    assert updated_service["Cijena"] == "350.00"

    search_response = client.get("/services?search=Veliki")

    assert search_response.status_code == 200

    search_results = search_response.json()

    assert len(search_results) == 1
    assert search_results[0]["NazivUsluge"] == "Veliki servis"

    delete_response = client.delete(f"/services/{service_id}")

    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/services/{service_id}")

    assert get_deleted_response.status_code == 404
