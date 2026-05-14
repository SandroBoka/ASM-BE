import pytest
from fastapi import HTTPException

from app.core.auth_types import EmployeeRole
from app.services.person_service import PersonService


class FakePersonRepository:
    def __init__(self):
        self.persons = []
        self.customers = []
        self.employees = []
        self.next_id = 1

    def get_all_persons(self):
        return self.persons

    def get_person_by_id(self, person_id):
        for person in self.persons:
            if person.IdOsobe == person_id:
                return person
        return None

    def get_person_by_email(self, email):
        for person in self.persons:
            if person.Email == email:
                return person
        return None

    def create_person(self, person):
        person.IdOsobe = self.next_id
        self.next_id += 1
        self.persons.append(person)
        return person

    def update_person(self, person):
        return person

    def delete_person(self, person):
        self.persons.remove(person)

    def get_customer_by_id(self, person_id):
        for customer in self.customers:
            if customer.IdOsobe == person_id:
                return customer
        return None

    def create_customer(self, customer):
        customer.person = self.get_person_by_id(customer.IdOsobe)
        self.customers.append(customer)
        return customer

    def update_customer(self, customer):
        return customer

    def delete_customer(self, customer):
        self.customers.remove(customer)

    def get_employee_by_id(self, person_id):
        for employee in self.employees:
            if employee.IdOsobe == person_id:
                return employee
        return None

    def create_employee(self, employee):
        employee.person = self.get_person_by_id(employee.IdOsobe)
        self.employees.append(employee)
        return employee

    def update_employee(self, employee):
        return employee

    def delete_employee(self, employee):
        self.employees.remove(employee)


def test_get_all_persons_returns_repository_persons():
    repository = FakePersonRepository()
    service = PersonService(repository)

    first_customer = service.create_customer(
        ime="Ivan",
        prezime="Horvat",
        email="ivan@example.com",
        telefon=None,
        lozinka="tajna123"
    )

    second_customer = service.create_customer(
        ime="Ana",
        prezime="Ivic",
        email="ana@example.com",
        telefon=None,
        lozinka="tajna456"
    )

    persons = service.get_all_persons()

    assert len(persons) == 2
    assert persons[0].IdOsobe == first_customer.IdOsobe
    assert persons[1].IdOsobe == second_customer.IdOsobe
    assert persons[0].Email == "ivan@example.com"
    assert persons[1].Email == "ana@example.com"


def test_create_customer_hashes_password():
    repository = FakePersonRepository()
    service = PersonService(repository)

    customer = service.create_customer(
        ime="Ivan",
        prezime="Horvat",
        email="ivan@example.com",
        telefon="091-111-222",
        lozinka="tajna123"
    )

    assert customer.IdOsobe == 1
    assert customer.person.Email == "ivan@example.com"
    assert customer.person.Lozinka != "tajna123"
    assert service.verify_password("tajna123", customer.person.Lozinka)


def test_create_customer_fails_when_email_exists():
    repository = FakePersonRepository()
    service = PersonService(repository)

    service.create_customer(
        ime="Ivan",
        prezime="Horvat",
        email="ivan@example.com",
        telefon=None,
        lozinka="tajna123"
    )

    with pytest.raises(HTTPException) as error:
        service.create_customer(
            ime="Ana",
            prezime="Ivic",
            email="ivan@example.com",
            telefon=None,
            lozinka="tajna456"
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Email je već u uporabi."


def test_update_employee_updates_person_data_without_role():
    repository = FakePersonRepository()
    service = PersonService(repository)

    employee = service.create_employee(
        ime="Marko",
        prezime="Novak",
        email="marko@example.com",
        telefon=None,
        lozinka="tajna123",
        uloga=EmployeeRole.SERVISER
    )

    updated_employee = service.update_employee(
        person_id=employee.IdOsobe,
        ime="Petar",
        prezime=None,
        email=None,
        telefon="098-555-666",
        lozinka=None
    )

    assert updated_employee.person.Ime == "Petar"
    assert updated_employee.person.Telefon == "098-555-666"
    assert updated_employee.Uloga == "serviser"


def test_update_employee_role_only():
    repository = FakePersonRepository()
    service = PersonService(repository)

    employee = service.create_employee(
        ime="Luka",
        prezime="Juric",
        email="luka@example.com",
        telefon=None,
        lozinka="tajna123",
        uloga=EmployeeRole.SERVISER
    )

    updated_employee = service.update_employee_role(
        person_id=employee.IdOsobe,
        uloga=EmployeeRole.VODITELJ
    )

    assert updated_employee.Uloga == "voditelj"
