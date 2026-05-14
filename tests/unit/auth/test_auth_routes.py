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


def create_customer():
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

    return response.json()


def login_customer():
    create_customer()

    response = client.post(
        "/auth/login",
        json={
            "Email": "ivan@example.com",
            "Lozinka": "tajna123"
        }
    )

    assert response.status_code == 200

    return response.json()


def test_login_api_returns_tokens_and_user():
    create_customer()

    response = client.post(
        "/auth/login",
        json={
            "Email": "ivan@example.com",
            "Lozinka": "tajna123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.access_token_expire_minutes * 60
    assert data["user"]["Email"] == "ivan@example.com"
    assert data["user"]["TipKorisnika"] == "customer"
    assert data["user"]["Uloga"] is None


def test_login_api_rejects_invalid_password():
    create_customer()

    response = client.post(
        "/auth/login",
        json={
            "Email": "ivan@example.com",
            "Lozinka": "wrong-password"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Neispravan email ili lozinka"


def test_me_api_returns_current_user_for_valid_access_token():
    login_response = login_customer()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {login_response['access_token']}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["Email"] == "ivan@example.com"
    assert data["TipKorisnika"] == "customer"


def test_me_api_requires_access_token():
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_api_returns_new_tokens():
    login_response = login_customer()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_response["refresh_token"]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["refresh_token"] != login_response["refresh_token"]
    assert data["user"]["Email"] == "ivan@example.com"


def test_logout_api_revokes_refresh_token():
    login_response = login_customer()

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": login_response["refresh_token"]
        }
    )

    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_response["refresh_token"]
        }
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Refresh token je opozvan"
