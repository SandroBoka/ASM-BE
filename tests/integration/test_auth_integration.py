from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
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
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_full_customer_auth_flow():
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

    login_response = client.post(
        "/auth/login",
        json={
            "Email": "ivan@example.com",
            "Lozinka": "tajna123"
        }
    )

    assert login_response.status_code == 200

    login_data = login_response.json()
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    assert login_data["user"]["Email"] == "ivan@example.com"
    assert login_data["user"]["TipKorisnika"] == "customer"

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert me_response.status_code == 200
    assert me_response.json()["Email"] == "ivan@example.com"

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert refresh_data["access_token"] is not None
    assert refresh_data["refresh_token"] != refresh_token
    assert refresh_data["user"]["Email"] == "ivan@example.com"

    old_refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert old_refresh_response.status_code == 401
    assert old_refresh_response.json()["detail"] == "Refresh token je opozvan"

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_data["refresh_token"]
        }
    )

    assert logout_response.status_code == 204

    refresh_after_logout_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_data["refresh_token"]
        }
    )

    assert refresh_after_logout_response.status_code == 401
    assert refresh_after_logout_response.json()["detail"] == "Refresh token je opozvan"
