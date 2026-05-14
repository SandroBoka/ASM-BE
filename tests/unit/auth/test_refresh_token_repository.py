from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.db.database import Base
from app.models.person import Person
from app.models.refresh_token import RefreshToken
from app.repositories.person_repository import PersonRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def create_person(db) -> Person:
    repository = PersonRepository(db)

    return repository.create_person(Person(
        Ime="Ivan",
        Prezime="Horvat",
        Email="ivan@example.com",
        Telefon=None,
        Lozinka="hashed-password"
    ))


def create_refresh_token(repository: RefreshTokenRepository, person_id: int) -> RefreshToken:
    return repository.create_refresh_token(RefreshToken(
        IdOsobe=person_id,
        TokenHash="token-hash",
        IstekaoU=datetime.now(timezone.utc) + timedelta(days=14),
        Opozvan=False
    ))


def test_create_and_get_refresh_token_by_hash():
    db = TestingSessionLocal()
    repository = RefreshTokenRepository(db)
    person = create_person(db)

    refresh_token = create_refresh_token(repository, person.IdOsobe)
    found_token = repository.get_refresh_token_by_hash("token-hash")

    assert refresh_token.IdRefreshTokena is not None
    assert found_token is not None
    assert found_token.IdRefreshTokena == refresh_token.IdRefreshTokena
    assert found_token.IdOsobe == person.IdOsobe
    assert found_token.Opozvan is False

    db.close()


def test_revoke_refresh_token():
    db = TestingSessionLocal()
    repository = RefreshTokenRepository(db)
    person = create_person(db)
    refresh_token = create_refresh_token(repository, person.IdOsobe)

    revoked_token = repository.revoke_refresh_token(refresh_token)

    assert revoked_token.Opozvan is True

    db.close()


def test_revoke_all_for_person():
    db = TestingSessionLocal()
    repository = RefreshTokenRepository(db)
    person = create_person(db)

    first_token = create_refresh_token(repository, person.IdOsobe)
    second_token = repository.create_refresh_token(RefreshToken(
        IdOsobe=person.IdOsobe,
        TokenHash="second-token-hash",
        IstekaoU=datetime.now(timezone.utc) + timedelta(days=14),
        Opozvan=False
    ))

    repository.revoke_all_for_person(person.IdOsobe)

    refreshed_first_token = repository.get_refresh_token_by_hash(first_token.TokenHash)
    refreshed_second_token = repository.get_refresh_token_by_hash(second_token.TokenHash)

    assert refreshed_first_token is not None
    assert refreshed_first_token.Opozvan is True
    assert refreshed_second_token is not None
    assert refreshed_second_token.Opozvan is True

    db.close()
