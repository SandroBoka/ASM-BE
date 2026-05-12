from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.person import Customer, Person
from app.models.vehicle import Vehicle
from app.repositories.person_repository import PersonRepository
from app.repositories.vehicle_repository import VehicleRepository

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


def create_customer(db) -> Customer:
    person_repository = PersonRepository(db)

    person = person_repository.create_person(Person(
        Ime="Ivan",
        Prezime="Horvat",
        Email="ivan@example.com",
        Telefon="091-111-222",
        Lozinka="hashed-password"
    ))

    return person_repository.create_customer(Customer(IdOsobe=person.IdOsobe))


def create_vehicle(
        repository: VehicleRepository,
        person_id: int,
        registration: str = "ZG-123-AB"
) -> Vehicle:
    return repository.create(Vehicle(
        Marka="Volkswagen",
        Model="Golf",
        Godina=2018,
        VrstaMotora="diesel",
        RegOznaka=registration,
        IdOsobe=person_id
    ))


def test_create_vehicle_in_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    vehicle = create_vehicle(repository, customer.IdOsobe)

    assert vehicle.IdVozila is not None
    assert vehicle.Marka == "Volkswagen"
    assert vehicle.RegOznaka == "ZG-123-AB"
    assert vehicle.IdOsobe == customer.IdOsobe

    db.close()


def test_get_vehicle_by_id_from_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    vehicle = create_vehicle(repository, customer.IdOsobe)

    found_vehicle = repository.get_by_id(vehicle.IdVozila)

    assert found_vehicle is not None
    assert found_vehicle.IdVozila == vehicle.IdVozila
    assert found_vehicle.RegOznaka == "ZG-123-AB"

    db.close()


def test_get_vehicle_by_registration_from_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    vehicle = create_vehicle(repository, customer.IdOsobe)

    found_vehicle = repository.get_by_registration("ZG-123-AB")

    assert found_vehicle is not None
    assert found_vehicle.IdVozila == vehicle.IdVozila

    db.close()


def test_get_vehicles_by_customer_id_from_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    first_vehicle = create_vehicle(
        repository,
        customer.IdOsobe,
        registration="ZG-123-AB"
    )
    second_vehicle = create_vehicle(
        repository,
        customer.IdOsobe,
        registration="ZG-456-CD"
    )

    vehicles = repository.get_by_customer_id(customer.IdOsobe)

    assert [vehicle.IdVozila for vehicle in vehicles] == [
        first_vehicle.IdVozila,
        second_vehicle.IdVozila
    ]

    db.close()


def test_update_vehicle_in_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    vehicle = create_vehicle(repository, customer.IdOsobe)

    vehicle.Model = "Passat"
    vehicle.Godina = 2021
    vehicle.RegOznaka = "ZG-999-ZZ"

    updated_vehicle = repository.update(vehicle)

    assert updated_vehicle.Model == "Passat"
    assert updated_vehicle.Godina == 2021
    assert updated_vehicle.RegOznaka == "ZG-999-ZZ"

    db.close()


def test_delete_vehicle_from_database():
    db = TestingSessionLocal()
    customer = create_customer(db)
    repository = VehicleRepository(db)

    vehicle = create_vehicle(repository, customer.IdOsobe)
    vehicle_id = vehicle.IdVozila

    repository.delete(vehicle)

    deleted_vehicle = repository.get_by_id(vehicle_id)

    assert deleted_vehicle is None

    db.close()
