from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    NazivUsluge: str
    Opis: str | None = None
    Trajanje: int
    Cijena: Decimal


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    IdUsluge: int = Field(validation_alias="IdUsluge")

    model_config = ConfigDict(from_attributes=True)
