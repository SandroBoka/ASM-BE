from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class AppointmentChangeBase(BaseModel):
    IdRezervacije: int
    IdStarogTermina: int
    IdNovogTermina: int


class AppointmentChangeCreate(AppointmentChangeBase):
    pass


class AppointmentChangeProcess(BaseModel):
    Status: str
    KomentarZaposlenika: str | None = None
    IdOsobe_Zaposlenik: int


class AppointmentChangeRequest(BaseModel):
    IdRezervacije: int
    IdNovogTermina: int


class AppointmentChangeActionRequest(BaseModel):
    komentar: str | None = None


class AppointmentChangeUpdate(BaseModel):
    Status: str | None = None
    KomentarZaposlenika: str | None = None
    IdNovogTermina: int | None = None
    IdOsobe_Zaposlenik: int | None = None


class AppointmentChangeResponse(AppointmentChangeBase):
    IdZahtjevaPromjene: int = Field(validation_alias="IdZahtjevaPromjene")
    DatumZahtjeva: date
    Status: str
    KomentarZaposlenika: str | None = None
    IdOsobe_Zaposlenik: int | None = None

    model_config = ConfigDict(from_attributes=True)
