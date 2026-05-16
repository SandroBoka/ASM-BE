from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.service_schema import ServiceResponse


class ReservationServiceItemCreate(BaseModel):
    IdUsluge: int
    Kolicina: int = 1


class ReservationServiceItemResponse(BaseModel):
    Kolicina: int
    service: ServiceResponse

    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
    IdOsobe_Korisnik: int
    IdTermina: int
    IdVozila: int
    KilometrazaVozila: int
    OpisProblema: str
    services: list[ReservationServiceItemCreate]


class ReservationProcess(BaseModel):
    Status: str
    KomentarZaposlenika: str | None = None
    IdOsobe_Zaposlenik: int


class ReservationActionRequest(BaseModel):
    komentar: str | None = None


class ReservationUpdate(BaseModel):
    Status: str | None = None
    KilometrazaVozila: int | None = None
    OpisProblema: str | None = None
    KomentarZaposlenika: str | None = None
    IdTermina: int | None = None
    IdVozila: int | None = None
    IdOsobe_Zaposlenik: int | None = None


class ReservationResponse(BaseModel):
    IdRezervacije: int = Field(validation_alias="IdRezervacije")
    DatumKreiranja: date
    Status: str
    KilometrazaVozila: int
    OpisProblema: str
    KomentarZaposlenika: str | None = None
    IdOsobe_Korisnik: int
    IdTermina: int
    IdVozila: int
    IdOsobe_Zaposlenik: int | None = None
    services: list[ReservationServiceItemResponse] = Field(
        default_factory=list,
        validation_alias="reservation_services",
    )

    model_config = ConfigDict(from_attributes=True)
