from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.service import Service
from app.repositories.service_repository import ServiceRepository

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


def test_create_service_in_database():
    db = TestingSessionLocal()
    repository = ServiceRepository(db)

    service = Service(
        NazivUsluge="Redovni servis",
        Opis="Zamjena ulja i filtera",
        Trajanje=60,
        Cijena=150
    )

    created_service = repository.create(service)

    assert created_service.IdUsluge is not None
    assert created_service.NazivUsluge == "Redovni servis"

    db.close()


def test_get_service_by_id_from_database():
    db = TestingSessionLocal()
    repository = ServiceRepository(db)

    service = Service(
        NazivUsluge="Dijagnostika",
        Opis="Kompjuterska dijagnostika",
        Trajanje=30,
        Cijena=50
    )

    created_service = repository.create(service)

    found_service = repository.get_by_id(created_service.IdUsluge)

    assert found_service is not None
    assert found_service.IdUsluge == created_service.IdUsluge
    assert found_service.NazivUsluge == "Dijagnostika"

    db.close()


def test_search_services_in_database():
    db = TestingSessionLocal()
    repository = ServiceRepository(db)

    repository.create(Service(
        NazivUsluge="Redovni servis",
        Opis=None,
        Trajanje=60,
        Cijena=150
    ))

    repository.create(Service(
        NazivUsluge="Dijagnostika",
        Opis=None,
        Trajanje=30,
        Cijena=50
    ))

    results = repository.get_all(search="servis")

    assert len(results) == 1
    assert results[0].NazivUsluge == "Redovni servis"

    db.close()


def test_update_service_in_database():
    db = TestingSessionLocal()
    repository = ServiceRepository(db)

    service = repository.create(Service(
        NazivUsluge="Stari naziv",
        Opis="Stari opis",
        Trajanje=30,
        Cijena=40
    ))

    service.NazivUsluge = "Novi naziv"
    service.Trajanje = 45
    service.Cijena = 60

    updated_service = repository.update(service)

    assert updated_service.NazivUsluge == "Novi naziv"
    assert updated_service.Trajanje == 45
    assert updated_service.Cijena == 60

    db.close()


def test_delete_service_from_database():
    db = TestingSessionLocal()
    repository = ServiceRepository(db)

    service = repository.create(Service(
        NazivUsluge="Brisanje usluge",
        Opis=None,
        Trajanje=30,
        Cijena=20
    ))

    service_id = service.IdUsluge

    repository.delete(service)

    deleted_service = repository.get_by_id(service_id)

    assert deleted_service is None

    db.close()
