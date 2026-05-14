from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.models.person import Customer, Employee, Person
from app.models.refresh_token import RefreshToken
from app.services.auth_service import AuthService
from app.services.person_service import PersonService


class FakePersonRepository:
    def __init__(self):
        self.persons = []

    def get_person_by_email(self, email):
        for person in self.persons:
            if person.Email == email:
                return person
        return None

    def get_person_by_id(self, person_id):
        for person in self.persons:
            if person.IdOsobe == person_id:
                return person
        return None


class FakeRefreshTokenRepository:
    def __init__(self):
        self.refresh_tokens = []
        self.next_id = 1

    def create_refresh_token(self, refresh_token):
        refresh_token.IdRefreshTokena = self.next_id
        self.next_id += 1
        self.refresh_tokens.append(refresh_token)
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash):
        for refresh_token in self.refresh_tokens:
            if refresh_token.TokenHash == token_hash:
                return refresh_token
        return None

    def update_refresh_token(self, refresh_token):
        return refresh_token

    def revoke_refresh_token(self, refresh_token):
        refresh_token.Opozvan = True
        return refresh_token


def create_customer_person() -> Person:
    person = Person(
        IdOsobe=1,
        Ime="Ivan",
        Prezime="Horvat",
        Email="ivan@example.com",
        Telefon=None,
        Lozinka=PersonService._hash_password("tajna123")
    )

    customer = Customer(IdOsobe=person.IdOsobe)
    customer.person = person
    person.customer_profile = customer

    return person


def create_employee_person() -> Person:
    person = Person(
        IdOsobe=2,
        Ime="Petar",
        Prezime="Novak",
        Email="petar@example.com",
        Telefon=None,
        Lozinka=PersonService._hash_password("tajna456")
    )

    employee = Employee(IdOsobe=person.IdOsobe, Uloga="admin")
    employee.person = person
    person.employee_profile = employee

    return person


def create_service_with_person(person: Person):
    person_repository = FakePersonRepository()
    refresh_token_repository = FakeRefreshTokenRepository()
    person_repository.persons.append(person)

    return AuthService(person_repository, refresh_token_repository), refresh_token_repository


def test_login_returns_access_and_refresh_tokens_for_customer():
    person = create_customer_person()
    service, refresh_token_repository = create_service_with_person(person)

    response = service.login("ivan@example.com", "tajna123")

    payload = jwt.decode(
        response.access_token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    assert response.token_type == "bearer"
    assert response.refresh_token is not None
    assert response.expires_in == settings.access_token_expire_minutes * 60
    assert response.user.IdOsobe == person.IdOsobe
    assert response.user.TipKorisnika == "customer"
    assert response.user.Uloga is None
    assert payload["sub"] == str(person.IdOsobe)
    assert payload["type"] == "customer"
    assert len(refresh_token_repository.refresh_tokens) == 1


def test_login_returns_employee_role_in_user_and_token_payload():
    person = create_employee_person()
    service, _ = create_service_with_person(person)

    response = service.login("petar@example.com", "tajna456")

    payload = jwt.decode(
        response.access_token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    assert response.user.TipKorisnika == "employee"
    assert response.user.Uloga == "admin"
    assert payload["type"] == "employee"
    assert payload["role"] == "admin"


def test_login_fails_for_invalid_credentials():
    person = create_customer_person()
    service, _ = create_service_with_person(person)

    with pytest.raises(HTTPException) as error:
        service.login("ivan@example.com", "wrong-password")

    assert error.value.status_code == 401
    assert error.value.detail == "Neispravan email ili lozinka"


def test_refresh_rotates_refresh_token():
    person = create_customer_person()
    service, refresh_token_repository = create_service_with_person(person)

    login_response = service.login("ivan@example.com", "tajna123")
    old_refresh_token = refresh_token_repository.refresh_tokens[0]

    refresh_response = service.refresh(login_response.refresh_token)

    assert old_refresh_token.Opozvan is True
    assert refresh_response.refresh_token != login_response.refresh_token
    assert len(refresh_token_repository.refresh_tokens) == 2


def test_refresh_fails_when_token_is_revoked():
    person = create_customer_person()
    service, refresh_token_repository = create_service_with_person(person)

    login_response = service.login("ivan@example.com", "tajna123")
    refresh_token_repository.refresh_tokens[0].Opozvan = True

    with pytest.raises(HTTPException) as error:
        service.refresh(login_response.refresh_token)

    assert error.value.status_code == 401
    assert error.value.detail == "Refresh token je opozvan"


def test_refresh_fails_when_token_is_expired():
    person = create_customer_person()
    service, refresh_token_repository = create_service_with_person(person)

    plain_token = "expired-refresh-token"
    refresh_token_repository.create_refresh_token(RefreshToken(
        IdOsobe=person.IdOsobe,
        TokenHash=service._hash_refresh_token(plain_token),
        IstekaoU=datetime.now(timezone.utc) - timedelta(days=1),
        Opozvan=False
    ))

    with pytest.raises(HTTPException) as error:
        service.refresh(plain_token)

    assert error.value.status_code == 401
    assert error.value.detail == "Refresh token je istekao"


def test_logout_revokes_refresh_token():
    person = create_customer_person()
    service, refresh_token_repository = create_service_with_person(person)

    login_response = service.login("ivan@example.com", "tajna123")

    service.logout(login_response.refresh_token)

    assert refresh_token_repository.refresh_tokens[0].Opozvan is True
