from typing import cast

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, vehicle_id: int) -> Vehicle | None:
        return (
            self.db
            .query(Vehicle)
            .filter(Vehicle.IdVozila == vehicle_id)  # type: ignore[arg-type]
            .first()
        )

    def get_by_registration(self, registration: str) -> Vehicle | None:
        return (
            self.db
            .query(Vehicle)
            .filter(Vehicle.RegOznaka == registration)  # type: ignore[arg-type]
            .first()
        )

    def get_by_customer_id(self, customer_id: int) -> list[Vehicle]:
        return cast(
            list[Vehicle],
            self.db
            .query(Vehicle)
            .filter(Vehicle.IdOsobe == customer_id)  # type: ignore[arg-type]
            .order_by(Vehicle.IdVozila)
            .all()
        )

    def create(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def update(self, vehicle: Vehicle) -> Vehicle:
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        self.db.delete(vehicle)
        self.db.commit()
