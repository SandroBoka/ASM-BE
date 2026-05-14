from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.core.auth_types import EmployeeRole


class PersonBase(BaseModel):
    Ime: str
    Prezime: str
    Email: EmailStr
    Telefon: str | None = None


class PersonCreate(PersonBase):
    Lozinka: str


class PersonUpdate(BaseModel):
    Ime: str | None = None
    Prezime: str | None = None
    Email: EmailStr | None = None
    Telefon: str | None = None
    Lozinka: str | None = None


class PersonResponse(PersonBase):
    IdOsobe: int = Field(validation_alias="IdOsobe")

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(PersonCreate):
    pass


class CustomerUpdate(PersonUpdate):
    pass


class CustomerResponse(PersonResponse):
    pass


class EmployeeCreate(PersonCreate):
    Uloga: EmployeeRole = EmployeeRole.SERVISER


class EmployeeUpdate(PersonUpdate):
    pass


class EmployeeRoleUpdate(BaseModel):
    Uloga: EmployeeRole


class EmployeeResponse(PersonResponse):
    Uloga: EmployeeRole
