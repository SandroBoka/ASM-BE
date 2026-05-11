from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.person import Customer, Employee, Person
from app.repositories.person_repository import PersonRepository

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


def create_person(repository: PersonRepository, email: str = "ivan@example.com") -> Person:
    return repository.create_person(Person(
        Ime="Ivan",
        Prezime="Horvat",
        Email=email,
        Telefon="091-111-222",
        Lozinka="hashed-password"
    ))


def test_create_person_in_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    person = create_person(repository)

    assert person.IdOsobe is not None
    assert person.Ime == "Ivan"
    assert person.Email == "ivan@example.com"

    db.close()


def test_get_person_by_id_and_email_from_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    person = create_person(repository, email="ana@example.com")

    found_by_id = repository.get_person_by_id(person.IdOsobe)
    found_by_email = repository.get_person_by_email("ana@example.com")

    assert found_by_id is not None
    assert found_by_id.IdOsobe == person.IdOsobe
    assert found_by_email is not None
    assert found_by_email.IdOsobe == person.IdOsobe

    db.close()


def test_get_all_persons_ordered_by_id():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    first_person = create_person(repository, email="first@example.com")
    second_person = create_person(repository, email="second@example.com")

    persons = repository.get_all_persons()

    assert [person.IdOsobe for person in persons] == [
        first_person.IdOsobe,
        second_person.IdOsobe
    ]

    db.close()


def test_update_person_in_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    person = create_person(repository)

    person.Ime = "Ivica"
    person.Telefon = None

    updated_person = repository.update_person(person)

    assert updated_person.Ime == "Ivica"
    assert updated_person.Telefon is None

    db.close()


def test_create_and_get_customer_in_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    person = create_person(repository)
    customer = repository.create_customer(Customer(IdOsobe=person.IdOsobe))

    found_customer = repository.get_customer_by_id(person.IdOsobe)
    customers = repository.get_all_customers()

    assert customer.IdOsobe == person.IdOsobe
    assert found_customer is not None
    assert found_customer.person.Email == "ivan@example.com"
    assert [item.IdOsobe for item in customers] == [person.IdOsobe]

    db.close()


def test_create_update_and_get_employee_in_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    person = create_person(repository, email="petar@example.com")
    employee = repository.create_employee(Employee(
        IdOsobe=person.IdOsobe,
        Uloga="serviser"
    ))

    employee.Uloga = "voditelj"
    updated_employee = repository.update_employee(employee)
    found_employee = repository.get_employee_by_id(person.IdOsobe)
    employees = repository.get_all_employees()

    assert updated_employee.Uloga == "voditelj"
    assert found_employee is not None
    assert found_employee.person.Email == "petar@example.com"
    assert [item.IdOsobe for item in employees] == [person.IdOsobe]

    db.close()


def test_delete_customer_employee_and_person_from_database():
    db = TestingSessionLocal()
    repository = PersonRepository(db)

    customer_person = create_person(repository, email="customer@example.com")
    customer = repository.create_customer(Customer(IdOsobe=customer_person.IdOsobe))

    employee_person = create_person(repository, email="employee@example.com")
    employee = repository.create_employee(Employee(
        IdOsobe=employee_person.IdOsobe,
        Uloga="serviser"
    ))

    repository.delete_customer(customer)
    repository.delete_employee(employee)
    repository.delete_person(customer_person)
    repository.delete_person(employee_person)

    assert repository.get_customer_by_id(customer_person.IdOsobe) is None
    assert repository.get_employee_by_id(employee_person.IdOsobe) is None
    assert repository.get_person_by_id(customer_person.IdOsobe) is None
    assert repository.get_person_by_id(employee_person.IdOsobe) is None

    db.close()
