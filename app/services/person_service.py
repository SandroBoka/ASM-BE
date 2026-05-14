import bcrypt

from fastapi import HTTPException, status

from app.core.auth_types import EmployeeRole
from app.models.person import Customer, Employee, Person
from app.repositories.person_repository import PersonRepository


class PersonService:
    def __init__(self, repository: PersonRepository):
        self.repository = repository

    def get_all_persons(self) -> list[Person]:
        return self.repository.get_all_persons()

    def get_person_by_id(self, person_id: int) -> Person:
        person = self.repository.get_person_by_id(person_id)

        if person is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Osoba nije pronađena"
            )

        return person

    def get_customer_by_id(self, customer_id: int) -> Customer:
        customer = self.repository.get_customer_by_id(customer_id)

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Korisnik nije pronađen"
            )

        return customer

    def get_employee_by_id(self, employee_id: int) -> Employee:
        employee = self.repository.get_employee_by_id(employee_id)

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Zaposlenik nije pronađen"
            )

        return employee

    def create_customer(
            self,
            ime: str,
            prezime: str,
            email: str,
            telefon: str | None,
            lozinka: str
    ) -> Customer:
        self._validate_person_data(
            ime=ime,
            prezime=prezime,
            email=email,
            lozinka=lozinka
        )
        self._ensure_email_is_available(email)

        person = Person(
            Ime=ime.strip(),
            Prezime=prezime.strip(),
            Email=email.strip(),
            Telefon=telefon.strip() if telefon else None,
            Lozinka=self._hash_password(password=lozinka)
        )

        created_person = self.repository.create_person(person)

        customer = Customer(IdOsobe=created_person.IdOsobe)

        return self.repository.create_customer(customer)

    def create_employee(
            self,
            ime: str,
            prezime: str,
            email: str,
            telefon: str | None,
            lozinka: str,
            uloga: EmployeeRole = EmployeeRole.SERVISER
    ) -> Employee:
        self._validate_person_data(
            ime=ime,
            prezime=prezime,
            email=email,
            lozinka=lozinka
        )
        self._ensure_email_is_available(email)

        person = Person(
            Ime=ime.strip(),
            Prezime=prezime.strip(),
            Email=email.strip(),
            Telefon=telefon.strip() if telefon else None,
            Lozinka=self._hash_password(password=lozinka)
        )

        created_person = self.repository.create_person(person)

        employee = Employee(
            IdOsobe=created_person.IdOsobe,
            Uloga=uloga.value
        )

        return self.repository.create_employee(employee)

    def update_person(
            self,
            person_id: int,
            ime: str | None = None,
            prezime: str | None = None,
            email: str | None = None,
            telefon: str | None = None,
            lozinka: str | None = None
    ) -> Person:
        person = self.get_person_by_id(person_id)

        if email is not None and email.strip() != person.Email:
            self._ensure_email_is_available(email)
            person.Email = email.strip()

        if ime is not None:
            self._validate_required_text(ime, "Ime")
            person.Ime = ime.strip()

        if prezime is not None:
            self._validate_required_text(prezime, "Prezime")
            person.Prezime = prezime.strip()

        if telefon is not None:
            person.Telefon = telefon.strip() if telefon.strip() else None

        if lozinka is not None:
            self._validate_required_text(lozinka, "Lozinka")
            person.Lozinka = self._hash_password(lozinka)

        return self.repository.update_person(person)

    def update_employee_role(self, person_id: int, uloga: EmployeeRole) -> Employee:
        employee = self.get_employee_by_id(person_id)

        employee.Uloga = uloga.value

        return self.repository.update_employee(employee)

    def update_customer(
            self,
            person_id: int,
            ime: str | None = None,
            prezime: str | None = None,
            email: str | None = None,
            telefon: str | None = None,
            lozinka: str | None = None
    ) -> Customer:
        customer = self.get_customer_by_id(person_id)

        self.update_person(
            person_id=person_id,
            ime=ime,
            prezime=prezime,
            email=email,
            telefon=telefon,
            lozinka=lozinka
        )

        return customer

    def update_employee(
            self,
            person_id: int,
            ime: str | None = None,
            prezime: str | None = None,
            email: str | None = None,
            telefon: str | None = None,
            lozinka: str | None = None
    ) -> Employee:
        employee = self.get_employee_by_id(person_id)

        self.update_person(
            person_id=person_id,
            ime=ime,
            prezime=prezime,
            email=email,
            telefon=telefon,
            lozinka=lozinka
        )

        return employee

    def delete_person(self, person_id: int) -> None:
        person = self.get_person_by_id(person_id)
        self.repository.delete_person(person)

    def _ensure_email_is_available(self, email: str) -> None:
        existing_person = self.repository.get_person_by_email(email.strip())

        if existing_person is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email je već u uporabi."
            )

    def _validate_person_data(
            self,
            ime: str,
            prezime: str,
            email: str,
            lozinka: str
    ) -> None:
        self._validate_required_text(ime, "Ime")
        self._validate_required_text(prezime, "Prezime")
        self._validate_required_text(email, "Email")
        self._validate_required_text(lozinka, "Lozinka")

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} je obavezno polje."
            )

    @staticmethod
    def _hash_password(password: str) -> str:
        password_bytes = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        return hashed_password.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
