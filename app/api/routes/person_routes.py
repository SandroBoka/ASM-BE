from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_types import UserType
from app.db.database import get_db
from app.repositories.person_repository import PersonRepository
from app.schemas import AuthUserResponse
from app.schemas.person_schema import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
    EmployeeCreate,
    EmployeeRoleUpdate,
    EmployeeResponse,
    EmployeeUpdate,
    PersonResponse,
    PersonUpdate,
)
from app.services.person_service import PersonService
from app.models.person import Customer, Employee
from app.api.dependencies.auth import (
    ensure_admin_or_self,
    get_current_user,
    require_admin,
    require_employee
)

router = APIRouter(
    prefix="/persons",
    tags=["Persons"]
)


def get_person_service(db: Session = Depends(get_db)) -> PersonService:
    repository = PersonRepository(db)
    return PersonService(repository)


def customer_to_response(customer: Customer) -> dict:
    return {
        "IdOsobe": customer.IdOsobe,
        "Ime": customer.person.Ime,
        "Prezime": customer.person.Prezime,
        "Email": customer.person.Email,
        "Telefon": customer.person.Telefon,
    }


def employee_to_response(employee: Employee) -> dict:
    return {
        "IdOsobe": employee.IdOsobe,
        "Ime": employee.person.Ime,
        "Prezime": employee.person.Prezime,
        "Email": employee.person.Email,
        "Telefon": employee.person.Telefon,
        "Uloga": employee.Uloga,
    }


@router.get("", response_model=list[PersonResponse])
def get_all_persons(
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_employee)
):
    return service.get_all_persons()


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(
        person_id: int,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_employee)
):
    return service.get_person_by_id(person_id)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
        customer_id: int,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    if (
            current_user.TipKorisnika != UserType.EMPLOYEE
            and current_user.IdOsobe != customer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Možete pristupiti samo vlastitim podacima"
        )

    return customer_to_response(service.get_customer_by_id(customer_id))


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(
        employee_id: int,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_employee)
):
    return employee_to_response(service.get_employee_by_id(employee_id))


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
        request: CustomerCreate,
        service: PersonService = Depends(get_person_service)
):
    customer = service.create_customer(
        ime=request.Ime,
        prezime=request.Prezime,
        email=str(request.Email),
        telefon=request.Telefon,
        lozinka=request.Lozinka
    )

    return customer_to_response(customer)


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
        request: EmployeeCreate,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_admin)
):
    employee = service.create_employee(
        ime=request.Ime,
        prezime=request.Prezime,
        email=str(request.Email),
        telefon=request.Telefon,
        lozinka=request.Lozinka,
        uloga=request.Uloga
    )

    return employee_to_response(employee)


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
        person_id: int,
        request: PersonUpdate,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_admin)
):
    return service.update_person(
        person_id=person_id,
        ime=request.Ime,
        prezime=request.Prezime,
        email=str(request.Email) if request.Email is not None else None,
        telefon=request.Telefon,
        lozinka=request.Lozinka
    )


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
        customer_id: int,
        request: CustomerUpdate,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    ensure_admin_or_self(current_user, customer_id)

    customer = service.update_customer(
        person_id=customer_id,
        ime=request.Ime,
        prezime=request.Prezime,
        email=str(request.Email) if request.Email is not None else None,
        telefon=request.Telefon,
        lozinka=request.Lozinka
    )

    return customer_to_response(customer)


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(
        employee_id: int,
        request: EmployeeUpdate,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):
    ensure_admin_or_self(current_user, employee_id)

    employee = service.update_employee(
        person_id=employee_id,
        ime=request.Ime,
        prezime=request.Prezime,
        email=str(request.Email) if request.Email is not None else None,
        telefon=request.Telefon,
        lozinka=request.Lozinka
    )

    return employee_to_response(employee)


@router.patch("/employees/{employee_id}/role", response_model=EmployeeResponse)
def update_employee_role(
        employee_id: int,
        request: EmployeeRoleUpdate,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(require_admin)
):
    employee = service.update_employee_role(
        person_id=employee_id,
        uloga=request.Uloga
    )

    return employee_to_response(employee)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(
        person_id: int,
        service: PersonService = Depends(get_person_service),
        current_user: AuthUserResponse = Depends(get_current_user)
):

    ensure_admin_or_self(current_user, person_id)

    service.delete_person(person_id)
