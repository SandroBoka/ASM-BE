from typing import cast

from sqlalchemy.orm import Session

from app.models.appointment_change import AppointmentChange


class AppointmentChangeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_change_id: int) -> AppointmentChange | None:
        return (
            self.db
            .query(AppointmentChange)
            .filter(AppointmentChange.IdZahtjevaPromjene == appointment_change_id)  # type: ignore[arg-type]
            .first()
        )

    def get_all(self) -> list[AppointmentChange]:
        return cast(
            list[AppointmentChange],
            self.db
            .query(AppointmentChange)
            .order_by(
                AppointmentChange.DatumZahtjeva,
                AppointmentChange.IdZahtjevaPromjene
            )
            .all()
        )

    def get_by_reservation_id(
            self,
            reservation_id: int
    ) -> list[AppointmentChange]:
        return cast(
            list[AppointmentChange],
            self.db
            .query(AppointmentChange)
            .filter(AppointmentChange.IdRezervacije == reservation_id)  # type: ignore[arg-type]
            .order_by(
                AppointmentChange.DatumZahtjeva,
                AppointmentChange.IdZahtjevaPromjene
            )
            .all()
        )

    def get_by_status(self, status: str) -> list[AppointmentChange]:
        return cast(
            list[AppointmentChange],
            self.db
            .query(AppointmentChange)
            .filter(AppointmentChange.Status == status)  # type: ignore[arg-type]
            .order_by(
                AppointmentChange.DatumZahtjeva,
                AppointmentChange.IdZahtjevaPromjene
            )
            .all()
        )

    def create(
            self,
            appointment_change: AppointmentChange
    ) -> AppointmentChange:
        self.db.add(appointment_change)
        self.db.commit()
        self.db.refresh(appointment_change)
        return appointment_change

    def update(
            self,
            appointment_change: AppointmentChange
    ) -> AppointmentChange:
        self.db.commit()
        self.db.refresh(appointment_change)
        return appointment_change

    def delete(self, appointment_change: AppointmentChange) -> None:
        self.db.delete(appointment_change)
        self.db.commit()
