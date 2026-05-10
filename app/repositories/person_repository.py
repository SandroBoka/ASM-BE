from sqlalchemy.orm import Session
from typing import cast
from app.models.person import Customer, Employee, Person


class PersonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_person_by_id(self, person_id: int) -> Person | None:
        return (
            self.db
            .query(Person)
            .filter(Person.IdOsobe == person_id)  # type: ignore[arg-type]
            .first()
        )

    def get_person_by_email(self, email: str) -> Person | None:
        return (
            self.db
            .query(Person)
            .filter(Person.Email == email)  # type: ignore[arg-type]
            .first()
        )

    def get_all_persons(self) -> list[Person]:
        return cast(list[Person], self.db.query(Person).order_by(Person.IdOsobe).all())

    def create_person(self, person: Person) -> Person:
        self.db.add(person)
        self.db.commit()
        self.db.refresh(person)
        return person

    def update_person(self, person: Person) -> Person:
        self.db.commit()
        self.db.refresh(person)
        return person

    def delete_person(self, person: Person) -> None:
        self.db.delete(person)
        self.db.commit()

    def get_customer_by_id(self, person_id: int) -> Customer | None:
        return (
            self.db
            .query(Customer)
            .filter(Customer.IdOsobe == person_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all_customers(self) -> list[Customer]:
        return cast(
            list[Customer],
            self.db.query(Customer).order_by(Customer.IdOsobe).all()
        )

    def create_customer(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_customer(self, customer: Customer) -> Customer:
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete_customer(self, customer: Customer) -> None:
        self.db.delete(customer)
        self.db.commit()

    def get_employee_by_id(self, person_id: int) -> Employee | None:
        return (
            self.db
            .query(Employee)
            .filter(Employee.IdOsobe == person_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all_employees(self) -> list[Employee]:
        return cast(
            list[Employee],
            self.db.query(Employee).order_by(Employee.IdOsobe).all()
        )

    def create_employee(self, employee: Employee) -> Employee:
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update_employee(self, employee: Employee) -> Employee:
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete_employee(self, employee: Employee) -> None:
        self.db.delete(employee)
        self.db.commit()
