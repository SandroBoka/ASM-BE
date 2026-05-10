from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    Naslov: str
    Tekst: str
    IdOsobe: int
    IdRezervacije: int


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    Procitana: bool | None = None


class NotificationResponse(NotificationBase):
    IdObavijesti: int = Field(validation_alias="IdObavijesti")
    DatumSlanja: datetime
    Procitana: bool

    model_config = ConfigDict(from_attributes=True)
