from fastapi import HTTPException, status

from app.models.vehicle import Vehicle

from app.repositories.vehicle_repository import VehicleRepository


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self.repository = repository

    def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle:
        vehicle = self.repository.get_by_id(vehicle_id)

        if vehicle is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vozilo nije pronađeno."
            )

        return vehicle

    def get_vehicles_by_customer_id(self, customer_id: int) -> list[Vehicle]:
        return self.repository.get_by_customer_id(customer_id)

    def create_vehicle(
            self,
            marka: str,
            model: str,
            godina: int,
            vrsta_motora: str,
            reg_oznaka: str,
            id_osobe: int
    ) -> Vehicle:
        self._validate_vehicle_data(
            marka=marka,
            model=model,
            godina=godina,
            vrsta_motora=vrsta_motora,
            reg_oznaka=reg_oznaka
        )
        self._ensure_registration_is_available(reg_oznaka)

        vehicle = Vehicle(
            Marka=marka.strip(),
            Model=model.strip(),
            Godina=godina,
            VrstaMotora=vrsta_motora.strip(),
            RegOznaka=reg_oznaka.strip(),
            IdOsobe=id_osobe
        )

        return self.repository.create(vehicle)

    def update_vehicle(
            self,
            vehicle_id: int,
            marka: str,
            model: str,
            godina: int,
            vrsta_motora: str,
            reg_oznaka: str
    ) -> Vehicle:
        vehicle = self.get_vehicle_by_id(vehicle_id)

        self._validate_vehicle_data(
            marka=marka,
            model=model,
            godina=godina,
            vrsta_motora=vrsta_motora,
            reg_oznaka=reg_oznaka
        )

        normalized_registration = reg_oznaka.strip()

        if normalized_registration != vehicle.RegOznaka:
            self._ensure_registration_is_available(normalized_registration)

        vehicle.Marka = marka.strip()
        vehicle.Model = model.strip()
        vehicle.Godina = godina
        vehicle.VrstaMotora = vrsta_motora.strip()
        vehicle.RegOznaka = normalized_registration

        return self.repository.update(vehicle)

    def delete_vehicle(self, vehicle_id: int) -> None:
        vehicle = self.get_vehicle_by_id(vehicle_id)
        self.repository.delete(vehicle)

    def _validate_vehicle_data(
            self,
            marka: str,
            model: str,
            godina: int,
            vrsta_motora: str,
            reg_oznaka: str
    ) -> None:
        self._validate_required_text(marka, "Marka")
        self._validate_required_text(model, "Model")
        self._validate_required_text(vrsta_motora, "Vrsta motora")
        self._validate_required_text(reg_oznaka, "Registracijska oznaka")

        if godina < 1900 or godina > 2100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Godina vozila mora biti između 1900 i 2100."
            )

    def _ensure_registration_is_available(self, reg_oznaka: str) -> None:
        existing_vehicle = self.repository.get_by_registration(reg_oznaka.strip())

        if existing_vehicle is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registracijska oznaka je već u uporabi."
            )

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} je obavezno polje."
            )
