from pydantic import BaseModel, ConfigDict, Field


class VehicleBase(BaseModel):
    Marka: str
    Model: str
    Godina: int
    VrstaMotora: str
    RegOznaka: str


class VehicleCreate(VehicleBase):
    IdOsobe: int


class VehicleUpdate(BaseModel):
    Marka: str | None = None
    Model: str | None = None
    Godina: int | None = None
    VrstaMotora: str | None = None
    RegOznaka: str | None = None


class VehicleResponse(VehicleBase):
    IdVozila: int = Field(validation_alias="IdVozila")
    IdOsobe: int

    model_config = ConfigDict(from_attributes=True)
