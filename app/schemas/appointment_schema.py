from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class AppointmentBase(BaseModel):
    Datum: date
    VrijemeOd: time
    VrijemeDo: time
    Status: str = "slobodan"


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    Datum: date | None = None
    VrijemeOd: time | None = None
    VrijemeDo: time | None = None
    Status: str | None = None


class AppointmentResponse(AppointmentBase):
    IdTermina: int = Field(validation_alias="IdTermina")

    model_config = ConfigDict(from_attributes=True)


class AvailableAppointmentFilter(BaseModel):
    DatumOd: date | None = None
    DatumDo: date | None = None
